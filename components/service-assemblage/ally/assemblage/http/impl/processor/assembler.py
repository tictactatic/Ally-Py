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

REGEX_PLACE_HOLDER = re.compile('^\$\{(.+?)\}$')  # The regex used to identify and extract value markers.
PLACE_HOLDER_CONTENT = ''  # The values entry that marks the proxy side content.

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
    decode = requires(Callable)
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
        assert callable(assemblage.requestHandler), 'Invalid request handler %s' % assemblage.requestHandler
        
        blocks = iterWithInner(assemblage.main.indexes, group=GROUP_BLOCK)
        stack = [(False, assemblage.requestNode, self.prepare(assemblage.main), self.extractor, blocks)]
        while stack:
            isTrimmed, node, content, extractor, blocks = stack.pop()
            assert isinstance(node, RequestNode), 'Invalid request node %s' % node
            assert isinstance(node.requests, dict), 'Invalid requests %s' % node.requests
            assert isinstance(content, Content), 'Invalid content %s' % content
            assert isinstance(content.source, AdjustableStream), 'Invalid content source %s' % content.source
            assert callable(content.decode), 'Invalid content decode %s' % content.decode
            assert callable(extractor), 'Invalid extractor %s' % extractor
            
            while True:
                try: block, inner = next(blocks)
                except StopIteration:
                    # Providing the remaining bytes.
                    for byts in extractor(content): yield byts
                    break
                assert isinstance(block, Index), 'Invalid block %s' % block
                
                # Provide all bytes until start.
                for byts in extractor(content, block.start): yield byts
                if block.end == content.source.tell(): continue  # No block content to process.
                
                bnode = node.requests.get(block.value)
                if bnode is None: bnode = node.requests.get('*')
                if bnode is None:
                    if isTrimmed: content.source.discard(block.end)  # Skip the block bytes.
                    continue
                assert isinstance(bnode, RequestNode), 'Invalid request node %s' % bnode

                reference = findFor(inner, group=GROUP_URL)
                if not reference: continue  # No reference to process
                assert isinstance(reference, Index), 'Invalid index %s' % reference
                assert isinstance(reference.marker, Marker), 'Invalid index marker %s' % reference.marker
                
                clob = findFor(inner, group=GROUP_CLOB)
                if not bnode.requests and not clob: continue 
                # No requests to process for sub node and character blob to inject.
                
                preparers = listFor(inner, group=GROUP_PREPARE)
                preparers.append(reference)
                
                captures = self.capture(content, preparers)
                if captures is None: continue  # No captures available.
                assert isinstance(captures, dict), 'Invalid captures %s' % captures
                
                url = captures.pop(reference, None)
                if url is None: continue  # No URL available.
                url = content.decode(b''.join(url))
                
                bcontent = assemblage.requestHandler(url, bnode.parameters)
                assert isinstance(bcontent, Content), 'Invalid content %s' % bcontent
                if bcontent.errorStatus is not None:
                    assert log.debug('Error %s %s for %s', bcontent.errorStatus, bcontent.errorText, url) or True
                    injectors = self.injectorsForErrors(content, inner, captures, bcontent)
                    for byts in self.injector(injectors, content, block.end): yield byts
                    continue
                
                if clob:
                    assert isinstance(clob, Index), 'Invalid index %s' % clob
                    injectors = [(clob, self.obtain(content, clob.marker, captures, self.prepare(bcontent)))]
                    for byts in self.injector(injectors, content, block.end): yield byts
                    continue
                
                if not bcontent.indexes:
                    assert log.debug('No index at %s', url) or True
                    continue
                
                content.source.discard(block.end)  # Skip the block bytes.
                
                stack.append((isTrimmed, node, content, extractor, blocks))
                isTrimmed, node, content = True, bnode, self.prepare(bcontent)
                blocks = iterWithInner(content.indexes, group=GROUP_BLOCK)
                
                injectors = self.injectorsForAdjust(content, captures)
                extractor = partial(self.injector, injectors)
    
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
        
        @param injectors: list[(Index, list[bytes|Content]|tuple(bytes|Content)|None)]
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
                for byts in self.extractor(content, index.start): yield byts
                content.source.discard(index.end)  # We just need to remove the content to be injected.
                
                if value is not None:
                    assert isinstance(value, (list, tuple)), 'Invalid value %s' % value
                    for val in value:
                        if isinstance(val, Content):
                            for byts in self.extractor(val): yield byts
                        else:
                            assert isinstance(val, bytes), 'Invalid value %s' % val
                            yield val
                
        # We provide the remaining content.
        for byts in self.extractor(content, until): yield byts
        
    # --------------------------------------------------------------------
    
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
                
    def capture(self, content, capturers):
        '''
        Captures the provided index groups.

        @param content: Content
            The content to capture from.
        @param capturers: list[Index]
            The list of indexes to capture the values for, if the index is not of a capture action then the marker value
            is provided if there is one.
        @param current: integer
            The current index in the stream.
        @return: dictionary{Index: bytes}|None
            The dictionary containing as a key the index and as a value the captured bytes. Returns None if there is
            nothing to capture.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(capturers, list), 'Invalid capturers %s' % capturers
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        assert isinstance(content.source, AdjustableStream), 'Invalid content source %s' % content.source
        assert capturers, 'At least on capture index is required %s' % capturers
        
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
            if index.marker.action == ACTION_CAPTURE:
                value = content.encode(capture[index.start - offset: index.end - offset])
                if index.marker.values: value = self.obtain(content, index.marker, captures, value)
                else: value = (value,)
                captures[index] = value
            elif index.value is not None:
                captures[index] = (content.encode(index.value),)
            
        for index in capturers:
            if index.marker.action != ACTION_CAPTURE and index.value is None:
                if index.marker.values: captures[index] = self.obtain(content, index.marker, captures)
        
        content.source.rewind(capture)
        return captures
    
    def escape(self, marker, value):
        '''
        Escapes in the provided value based on the marker.
        
        @param marker: Marker
            The marker to use for escaping the value.
        @param value: string
            The value to be escaped.
        @return: string
            The escaped value.
        '''
        assert isinstance(marker, Marker), 'Invalid marker %s' % marker
        assert isinstance(value, str), 'Invalid value %s' % value
        
        if marker.replace:
            if marker.replaceMapping:
                def replace(match): return marker.replaceMapping.get(match.group(0), '')
            else: replace = marker.replaceValue
            return marker.replace.sub(replace, value)
        return value
    
    def obtain(self, content, marker, captures, value=None):
        '''
        Provides the value of the marker to be used for an injector.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(marker, Marker), 'Invalid marker %s' % marker
        assert isinstance(captures, dict), 'Invalid captures %s' % captures
        assert isinstance(marker.values, list), 'Invalid marker values %s' % marker.values
        assert marker.values, 'Required at least a value'
        
        values, current, isAdded = [], [], None
        for val in marker.values:
            if val == PLACE_HOLDER_CONTENT and not isAdded:
                if value is None: current.append(val)
                else:
                    if current: 
                        values.append(content.encode(''.join(current)))
                        current = []
                    if isinstance(value, str):
                        values.append(content.encode(self.escape(marker, value)))
                    else: values.append(value)
                isAdded = True
            else:
                match = REGEX_PLACE_HOLDER.match(val)
                if match:
                    name = match.groups()[0]
                    for index, replace in captures.items():
                        assert isinstance(index, Index), 'Invalid index %s' % index
                        assert isinstance(index.marker, Marker), 'Invalid index marker %s' % index.marker
                        if index.marker.name == name:
                            if replace is not None:
                                assert isinstance(replace, (list, tuple)), 'Invalid replace value %s' % replace
                                if current:
                                    values.append(content.encode(''.join(current)))
                                    current = []
                                values.extend(replace)
                            break
                        
                else: current.append(val)
                
        if current: values.append(content.encode(''.join(current)))
        
        if isAdded and isinstance(value, Content):
            # We need to adjust the value content encode in order to escape also the characters.
            assert isinstance(value, Content)
            oencode = value.encode
            def encode(content):
                if not isinstance(content, str): content = value.decode(content)
                content = self.escape(marker, content)
                return oencode(content)
            value.encode = encode
        
        return values
    
    # --------------------------------------------------------------------
    
    def injectorsForErrors(self, content, inner, captures, econtent):
        '''
        Provides the injectors list for errors.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(econtent, Content), 'Invalid error content %s' % econtent
        
        injectors = []
        for index in listFor(inner, group=GROUP_ERROR, action=ACTION_INJECT, hasValues=True):
            assert isinstance(index, Index), 'Invalid index %s' % index
            assert isinstance(index.marker, Marker), 'Invalid index maker %s' % index.marker
            
            value = None
            if index.marker.target == ERROR_STATUS:
                value = str(econtent.errorStatus)
            elif index.marker.target == ERROR_MESSAGE and econtent.errorText:
                value = str(econtent.errorText)
            injectors.append((index, self.obtain(content, index.marker, captures, value)))
                
        return injectors
    
    def injectorsForAdjust(self, content, captures):
        '''
        Provides the injectors for adjusting with captures.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(captures, dict), 'Invalid captures %s' % captures
        captures = {index.marker.id: replace for index, replace in captures.items()}
        
        injectors = []
        for index in listFor(content.indexes, group=GROUP_ADJUST, action=ACTION_INJECT):
            assert isinstance(index, Index), 'Invalid index %s' % index
            assert isinstance(index.marker, Marker), 'Invalid index maker %s' % index.marker
            if index.marker.sourceId is not None: replace = captures.get(index.marker.sourceId)
            else: replace = None
            injectors.append((index, replace))
        return injectors
