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
from ally.support.util_io import RewindingStream, IInputStream
from collections import Callable, Iterable
from functools import partial
import logging

# --------------------------------------------------------------------

GROUP_BLOCK = 'block'  # The group name for block.
GROUP_PREPARE = 'prepare'  # The group name for prepare.
GROUP_ADJUST = 'adjust'  # The group name for adjust.
GROUP_URL = 'URL'  # The group name for URL reference.
GROUP_ERROR = 'error'  # The group name for errors occurred while fetching URLs.

ACTION_INJECT = 'inject'  # The action name for inject.
ACTION_CAPTURE = 'capture'  # The action name for capture.

ERROR_STATUS = 'ERROR'  # The attribute name for error status.
ERROR_MESSAGE = 'ERROR_TEXT'  # The attribute name for error message.

MARKER_VALUE = '*'  # The marker to be used for injecting the attribute value.

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
            assert isinstance(content.source, RewindingStream), 'Invalid content source %s' % content.source
            assert callable(extractor), 'Invalid extractor %s' % extractor
            
            while True:
                try: block, inner = next(blocks)
                except StopIteration:
                    # Providing the remaining bytes.
                    for bytes in extractor(content): yield bytes
                    break

                assert isinstance(block, Index), 'Invalid block %s' % block
                reference = findFor(inner, group=GROUP_URL, action=ACTION_CAPTURE)
                if not reference: continue  # No reference to process
                assert isinstance(reference, Index), 'Invalid index %s' % reference
                assert isinstance(reference.marker, Marker), 'Invalid index marker %s' % reference.marker
                
                preparers = listFor(inner, group=GROUP_PREPARE, action=ACTION_CAPTURE)
                preparers.append(reference)
                
                # Provide all bytes until start.
                for bytes in extractor(content, block.start): yield bytes
                if block.end == content.source.tell(): continue  # No block content to process.
                
                bnode = node.requests.get(block.value)
                if bnode is None: bnode = node.requests.get('*')
                if bnode is None:
                    if isTrimmed: self.discard(content, block.end)  # Skip the block bytes.
                    else:
                        # Provide all block bytes as they are.
                        for bytes in extractor(content, block.end): yield bytes
                else:
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
                        errorStatus = findFor(inner, group=GROUP_ERROR, action=ACTION_INJECT, target=ERROR_STATUS)
                        if errorStatus:
                            assert isinstance(errorStatus, Index), 'Invalid index %s' % errorStatus
                            #TODO: remove
                            print(errorStatus)
                        # TODO: handle error
                        continue
                    if not bcontent.indexes:
                        assert log.debug('No index at %s', url) or True
                        # TODO: handle non rest content
                        continue
                    self.discard(content, block.end)  # Skip the remaining bytes from the capture
                    
                    stack.append((isTrimmed, node, content, extractor, blocks))
                    isTrimmed, node, content = True, bnode, self.prepare(bcontent)
                    blocks = iterWithInner(content.indexes, group=GROUP_BLOCK)
                    injectors = listFor(content.indexes, group=GROUP_ADJUST, action=ACTION_INJECT)
                    extractor = partial(self.injector, injectors, captures)
    
    def prepare(self, content):
        '''
        Prepare the content for compatibility.
        
        @param content: Content
            The content to process.
        @return: Content
            The processed provided content.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        if content.source is not None and not isinstance(content.source, RewindingStream):
            content.source = RewindingStream(content.source)
        
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
        assert isinstance(content.source, RewindingStream), 'Invalid content source %s' % content.source
        
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
                
    def injector(self, injectors, captures, content, until=None):
        '''
        Extracts from the stream the provided number of bytes and injects content if so required. 
        
        @param injectors: list[Index]
            The list of inject indexes to inject the values for.
        @param captures: dictionary{integer: bytes}
            The captures that provide the values to be injected.
        @param content: Content
            The content to extract from.
        @param until: integer|None
            The offset until to pull the bytes, if None it will pull all remaining bytes.
        @return: Iterable(bytes)
            Chunk size bytes pulled from the stream.
        '''
        assert isinstance(injectors, list), 'Invalid injectors %s' % injectors
        assert isinstance(captures, dict), 'Invalid captures %s' % captures
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        assert isinstance(content.source, RewindingStream), 'Invalid content source %s' % content.source
        assert until is None or isinstance(until, int), 'Invalid until offset %s' % until
        
        for index in injectors:
            assert isinstance(index, Index), 'Invalid index %s' % index
            assert isinstance(index.marker, Marker), 'Invalid index marker %s' % index.marker
            
            if index.start >= content.source.tell() and (until is None or index.end <= until):
                # We provide what is before the inject.
                for bytes in self.extractor(content, index.start): yield bytes
                self.discard(content, index.end)  # We just need to remove the content to be injected.
                
                if index.marker.sourceId is not None:
                    replace = captures.get(index.marker.sourceId)
                    if replace is not None: yield replace
                
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
        assert isinstance(content.source, RewindingStream), 'Invalid content source %s' % content.source
        
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
                
    def discard(self, content, until):
        '''
        Discard from the content source the provided number of bytes.
        
        @param content: Content
            The content to discard from.
        @param until: integer
            The offset until to discard bytes.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(content.source, RewindingStream), 'Invalid content source %s' % content.source
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
    
