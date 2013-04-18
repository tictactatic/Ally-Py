'''
Created on Mar 27, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assembler processor.
'''

from ally.assemblage.http.spec.assemblage import RequestNode, Index, \
    iterWithInner, listFor, Marker, findFor
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_io import AdjustableStream, IInputStream
from collections import Callable, Iterable
from functools import partial
import logging
import re

# --------------------------------------------------------------------

GROUP_BLOCK = 'block'  # The group name for block.
GROUP_PREPARE = 'prepare'  # The group name for prepare.
GROUP_ADJUST = 'adjust'  # The group name for adjust.
GROUP_URL = 'URL'  # The group name for URL reference.
GROUP_CLOB = 'clob'  # The group name for character blobs injection from reference URLs.
GROUP_ERROR = 'error'  # The group name for errors occurred while fetching URLs.

ACTION_INJECT = 'inject'  # The action name for inject.
ACTION_CAPTURE = 'capture'  # The action name for capture.

ERROR_STATUS = 'ERROR'  # The attribute name for error status.
ERROR_MESSAGE = 'ERROR_TEXT'  # The attribute name for error message.

REGEX_PLACE_HOLDER = re.compile('\$\{(\w+)\}')  # The regex used to identify and extract value markers.
CONTENT_MARKER = ''  # The values entry that marks the proxy side content.

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class ResponseContent(Context):
    '''
    The response content context. 
    '''
    # ---------------------------------------------------------------- Defined
    source = defines(Iterable, doc='''
    @rtype: Iterable
    The assembled content source.
    ''')
    
class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Required
    requestNode = requires(RequestNode)
    requestHandler = requires(Callable)
    decode = requires(Callable)
    main = requires(object)

class Content(Context):
    '''
    The assemblage content context.
    '''
    # ---------------------------------------------------------------- Required
    errorStatus = requires(int)
    errorText = requires(str)
    source = requires(IInputStream)
    encode = requires(Callable)
    indexes = requires(list)
    
# --------------------------------------------------------------------

@injected
class AssemblerHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the assembling.
    '''
    
    maximumBlockSize = 1024
    # The maximum block size in bytes before dispatching.
    
    def __init__(self):
        assert isinstance(self.maximumBlockSize, int), 'Invalid maximum block size %s' % self.maximumBlockSize
        super().__init__(Content=Content)

    def process(self, chain, responseCnt:ResponseContent, assemblage:Assemblage, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Assemble response content.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        assert isinstance(assemblage.main, Content), 'Invalid main content %s' % assemblage.main
        assert assemblage.main.errorStatus is None, 'Invalid main content %s, has an error status' % assemblage.main
        
        if assemblage.main.indexes is None: return  # No indexes to process
        
        responseCnt.source = self.assemble(assemblage)
        chain.proceed()
        
    # --------------------------------------------------------------------
    
    def assemble(self, assemblage):
        '''
        Assembles the content.
        
        @param assemblage: Assemblage
            The assemblage to use for assembly.
        @return: Iterable(bytes)
            The assembled content in chunk bytes.
        '''
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        assert isinstance(assemblage.main, Content), 'Invalid assemblage main content %s' % assemblage.main
        assert callable(assemblage.decode), 'Invalid assemblage decode %s' % assemblage.decode
        assert callable(assemblage.requestHandler), 'Invalid request handler %s' % assemblage.requestHandler
        
        blocks = iterWithInner(assemblage.main.indexes, group=GROUP_BLOCK)
        stack = [(False, assemblage.requestNode, self.prepare(assemblage.main), self.extractor, blocks)]
        while stack:
            isTrimmed, node, content, extractor, blocks = stack.pop()
            assert isinstance(node, RequestNode), 'Invalid request node %s' % node
            assert isinstance(node.requests, dict), 'Invalid requests %s' % node.requests
            assert isinstance(content, Content), 'Invalid content %s' % content
            assert isinstance(content.source, AdjustableStream), 'Invalid content source %s' % content.source
            assert callable(extractor), 'Invalid extractor %s' % extractor
            
            while True:
                try: block, inner = next(blocks)
                except StopIteration:
                    # Providing the remaining bytes.
                    for bytes in extractor(content): yield bytes
                    break
                assert isinstance(block, Index), 'Invalid block %s' % block
                
                # Provide all bytes until start.
                for bytes in extractor(content, block.start): yield bytes
                if block.end == content.source.tell(): continue  # No block content to process.
                
                bnode = node.requests.get(block.value)
                if bnode is None: bnode = node.requests.get('*')
                if bnode is None:
                    if isTrimmed: content.source.discard(block.end)  # Skip the block bytes.
                    continue

                reference = findFor(inner, group=GROUP_URL, action=ACTION_CAPTURE)
                if not reference: continue  # No reference to process
                assert isinstance(reference, Index), 'Invalid index %s' % reference
                assert isinstance(reference.marker, Marker), 'Invalid index marker %s' % reference.marker
                
                preparers = listFor(inner, group=GROUP_PREPARE, action=ACTION_CAPTURE)
                preparers.append(reference)
                
                assert isinstance(bnode, RequestNode), 'Invalid request node %s' % bnode
                if not bnode.requests: continue  # No requests to process for sub node.
                captures = self.capture(preparers, content)
                if captures is None: continue  # No captures available.
                
                assert isinstance(captures, dict), 'Invalid captures %s' % captures
                
                url = assemblage.decode(captures.pop(reference.marker.id))
                bcontent = assemblage.requestHandler(url, bnode.parameters)
                assert isinstance(bcontent, Content), 'Invalid content %s' % bcontent
                if bcontent.errorStatus is not None:
                    assert log.debug('Error %s %s for %s', bcontent.errorStatus, bcontent.errorText, url) or True
                    injectors = self.injectorsForErrors(inner, content, bcontent)
                    for bytes in self.injector(injectors, content, block.end): yield bytes
                    continue
                if not bcontent.indexes:
                    assert log.debug('No index at %s', url) or True
                    injectors = self.injectorsForCLOB(inner, preparers, bcontent, captures)
                    if injectors:
                        content.source.discard(block.end)  # Skip the block bytes.
                        for bytes in self.injector(injectors, content, block.end): yield bytes
                    # TODO: handle non rest content
                    continue
                content.source.discard(block.end)  # Skip the block bytes.
                
                stack.append((isTrimmed, node, content, extractor, blocks))
                isTrimmed, node, content = True, bnode, self.prepare(bcontent)
                blocks = iterWithInner(content.indexes, group=GROUP_BLOCK)
                
                injectors = self.injectorsForCaptures(content, captures)
                extractor = partial(self.injector, injectors)
    
    def prepare(self, content):
        '''
        Prepare the content for compatibility.
        
        @param content: Content
            The content to process.
        @return: Content
            The processed provided content.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        if content.source is not None and not isinstance(content.source, AdjustableStream):
            content.source = AdjustableStream(content.source)
        
        return content
    
    def extractor(self, content, until=None):
        '''
        Extracts from the content stream the provided number of bytes.
        
        @param content: Content
            The content to extract from.
        @param until: integer|None
            The offset until to pull the bytes, if None it will pull all remaining bytes.
        @return: Iterable(bytes)
            Chunk size bytes pulled from the stream.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        assert isinstance(content.source, AdjustableStream), 'Invalid content source %s' % content.source
        
        if until is None:
            while True:
                block = content.source.read(self.maximumBlockSize)
                if block == b'': break
                yield content.encode(block)
        else:
            assert isinstance(until, int), 'Invalid until offset %s' % until
            if until < content.source.tell():
                raise IOError('Invalid stream offset %s, expected a value less then %s' % (content.source.tell(), until))
            nbytes = until - content.source.tell()
            if nbytes == 0: return
            while nbytes > 0:
                if nbytes <= self.maximumBlockSize: block = content.source.read(nbytes)
                else: block = content.source.read(self.maximumBlockSize)
                if block == b'': raise IOError('The stream is missing %s bytes' % nbytes)
                nbytes -= len(block)
                yield content.encode(block)
                
    def injector(self, injectors, content, until=None):
        '''
        Extracts from the stream the provided number of bytes and injects content if so required. 
        
        @param injectors: list[(Index, bytes|None)]
            The list of tuples with inject index and the value on the second position.
        @param content: Content
            The content to extract from.
        @param until: integer|None
            The offset until to pull the bytes, if None it will pull all remaining bytes.
        @return: Iterable(bytes)
            Chunk size bytes pulled from the stream.
        '''
        assert isinstance(injectors, list), 'Invalid injectors %s' % injectors
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        assert isinstance(content.source, AdjustableStream), 'Invalid content source %s' % content.source
        assert until is None or isinstance(until, int), 'Invalid until offset %s' % until
        
        for index, value in injectors:
            assert isinstance(index, Index), 'Invalid index %s' % index
            assert isinstance(index.marker, Marker), 'Invalid index marker %s' % index.marker
            
            if index.start >= content.source.tell() and (until is None or index.end <= until):
                # We provide what is before the inject.
                for bytes in self.extractor(content, index.start): yield bytes
                content.source.discard(index.end)  # We just need to remove the content to be injected.
                
                if value is not None: yield value
                
        # We provide the remaining content.
        for bytes in self.extractor(content, until): yield bytes
                
    def capture(self, capturers, content):
        '''
        Captures the provided index groups.

        @param capturers: list[Index]
            The list of capturers indexes to capture the values for.
        @param content: Content
            The content to capture from.
        @param current: integer
            The current index in the stream.
        @return: dictionary{integer: bytes}|None
            The dictionary containing as a key the marker id and as a value the captured bytes. Returns None if there is
            nothing to capture.
        '''
        assert isinstance(capturers, list), 'Invalid capturers %s' % capturers
        assert capturers, 'At least on capture index is required %s' % capturers
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        assert isinstance(content.source, AdjustableStream), 'Invalid content source %s' % content.source
        
        ecapture = max(capturers, key=lambda group: group.end)
        assert isinstance(ecapture, Index), 'Invalid index %s' % ecapture
        if ecapture.end < content.source.tell():
            raise IOError('Invalid stream offset %s, expected a value less then %s' % (content.source.tell(), ecapture.end))
        
        nbytes = ecapture.end - content.source.tell()
        if nbytes == 0: return
        offset = content.source.tell()
        capture = content.source.read(nbytes)
        
        captures = {}
        for index in capturers:
            assert isinstance(index, Index), 'Invalid index %s' % index
            assert isinstance(index.marker, Marker), 'Invalid index marker %s' % index.marker
            captures[index.marker.id] = content.encode(capture[index.start - offset: index.end - offset])
        
        content.source.rewind(capture)
        return captures
            
    def escape(self, marker, value):
        '''
        Escapes the provided value based on 
        
        @param marker: Marker
            The marker to use for escaping the value.
        @param value: string
            The value to be escaped.
        @return: string
            The escaped value.
        '''
        assert isinstance(marker, Marker), 'Invalid marker %s' % marker
        assert isinstance(value, str), 'Invalid value %s' % value
        
        if marker.escapes:
            assert isinstance(marker.escapes, dict), 'Invalid escapes %s' % marker.escapes
            for replaced, replacer in marker.escapes.items(): value = value.replace(replaced, replacer)

        return value
    
    # --------------------------------------------------------------------
    
    def injectorsForErrors(self, inner, content, econtent):
        '''
        Provides the injectors list for errors.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(econtent, Content), 'Invalid error content %s' % econtent
        
        injectors = []
        for index in listFor(inner, group=GROUP_ERROR, action=ACTION_INJECT):
            assert isinstance(index, Index), 'Invalid index %s' % index
            assert isinstance(index.marker, Marker), 'Invalid index maker %s' % index.marker
            if index.marker.values:
                value = None
                if index.marker.target == ERROR_STATUS:
                    value = self.escape(index.marker, str(econtent.errorStatus))
                elif index.marker.target == ERROR_MESSAGE and econtent.errorText:
                    value = self.escape(index.marker, econtent.errorText)
                if value:
                    values = list(index.marker.values)
                    try: values[values.index(CONTENT_MARKER)] = value
                    except ValueError: pass
                    injectors.append((index, content.encode(''.join(values))))
        return injectors
    
    def injectorsForCaptures(self, content, captures):
        '''
        Provides the injectors for adjusting captures.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(captures, dict), 'Invalid captures %s' % captures
        
        injectors = []
        for index in listFor(content.indexes, group=GROUP_ADJUST, action=ACTION_INJECT):
            assert isinstance(index, Index), 'Invalid index %s' % index
            assert isinstance(index.marker, Marker), 'Invalid index maker %s' % index.marker
            if index.marker.sourceId is not None: value = captures.get(index.marker.sourceId)
            else: value = None
            injectors.append((index, value))
        return injectors

    def injectorsForCLOB(self, inner, preparers, content, captures):
        '''
        Provides the injectors for character blob injection.
        '''
        assert isinstance(preparers, list), 'Invalid preparers %s' % preparers
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(captures, dict), 'Invalid captures %s' % captures
        
        clob = findFor(inner, group=GROUP_CLOB, action=ACTION_INJECT)
        assert isinstance(clob, Index), 'Invalid index %s' % clob
        assert isinstance(clob.marker, Marker), 'Invalid index maker %s' % clob.marker
        assert isinstance(clob.marker.values, Marker), 'Invalid index maker %s' % clob.marker
            
        values, current = [], []
        for value in clob.marker.values:
            if value == CONTENT_MARKER:
                if current:
                    values.append(content.encode(''.join(current)))
                    current = []
                values.append(content)
            else:
                match = REGEX_PLACE_HOLDER.match(value)
                if match:
                    name = match.groups(0)
                    for index in preparers:
                        assert isinstance(index, Index), 'Invalid index %s' % index
                        assert isinstance(index.marker, Marker), 'Invalid index maker %s' % index.marker
                        if index.marker.name == name: break
                    else: continue  # There is no value available for place holder.
                    
                    replace = captures.get(index.marker.id)
                    if replace:
                        if current:
                            values.append(content.encode(''.join(current)))
                            current = []
                        values.append(replace)
                        
                else: current.append(value)
        if current: values.append(content.encode(''.join(current)))
                
        return [(clob, values)]
