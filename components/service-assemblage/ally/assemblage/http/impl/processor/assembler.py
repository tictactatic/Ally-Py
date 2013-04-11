'''
Created on Mar 27, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assembler processor.
'''

from ally.assemblage.http.spec.assemblage import RequestNode, Index
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_io import IInputStreamCT
from collections import Callable, Iterable
from functools import partial
import logging

# --------------------------------------------------------------------

GROUP_VALUE_REFERENCE = 'reference'  # Indicates that the captured value contains a reference.

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
    source = requires(IInputStreamCT)
    encode = requires(Callable)
    indexes = requires(list)
    
# --------------------------------------------------------------------

@injected
class AssemblerHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the assembling.
    '''
    
    maximumBlockSize = 9
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
        
        stack = [(False, assemblage.requestNode, assemblage.main, self.extractor, self.iterBlocks(assemblage.main.indexes))]
        while stack:
            isTrimmed, node, content, extractor, blocks = stack.pop()
            assert isinstance(node, RequestNode), 'Invalid request node %s' % node
            assert isinstance(node.requests, dict), 'Invalid requests %s' % node.requests
            assert isinstance(content, Content), 'Invalid content %s' % content
            assert isinstance(content.source, IInputStreamCT), 'Invalid content source %s' % content.source
            assert callable(extractor), 'Invalid extractor %s' % extractor
            
            while True:
                try: block, groups = next(blocks)
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
                    if isTrimmed: self.discard(content, block.end)  # Skip the block bytes.
                    else:
                        # Provide all block bytes as they are.
                        for bytes in extractor(content, block.end): yield bytes
                else:
                    assert isinstance(bnode, RequestNode), 'Invalid request node %s' % bnode
                    for gref in groups:
                        assert isinstance(gref, Index), 'Invalid index %s' % gref
                        if gref.value == GROUP_VALUE_REFERENCE: break
                    else:
                        # If there is no reference there is no reference to fetch then just provide the group as it is.
                        for bytes in extractor(content, block.end): yield bytes
                        continue
                    
                    capture = self.capture(groups, content)
                    if capture is None: continue
                    cbytes, captures = capture
                    
                    url = assemblage.decode(captures[GROUP_VALUE_REFERENCE])
                    bcontent = assemblage.requestHandler(url, bnode.parameters)
                    assert isinstance(bcontent, Content), 'Invalid content %s' % bcontent
                    if bcontent.errorStatus is not None:
                        # TODO: handle error
                        yield cbytes
                        continue
                    if not bcontent.indexes:
                        # TODO: handle non rest content
                        yield cbytes
                        continue
                    self.discard(content, block.end)  # Skip the remaining bytes from the capture
                    
                    stack.append((isTrimmed, node, content, extractor, blocks))
                    isTrimmed, node, content, blocks = False, bnode, bcontent, self.iterBlocks(bcontent.indexes)
                    extractor = partial(self.injector, self.listInject(bcontent.indexes), captures)
        
    def iterBlocks(self, indexes):
        '''
        Iterates the blocks indexes.
        
        @param indexes: Iterable(Index)
            The iterable of indexes to search in.
        @return: Iterable(tuple(Index, list[Index]))
            Iterates the tuples containing on the first position the block index and on the second the list
            of sub indexes of group capture type of the block index.
        '''
        assert isinstance(indexes, Iterable), 'Invalid indexes %s' % indexes
        
        indexes = iter(indexes)
        try: index = next(indexes)
        except StopIteration: return
        while True:
            assert isinstance(index, Index), 'Invalid index %s' % index
            if index.isBlock:
                groups, finalized = [], False
                while True:
                    try: sindex = next(indexes)
                    except StopIteration:
                        finalized = True
                        break
                    assert isinstance(sindex, Index), 'Invalid index %s' % sindex
                    if sindex.end <= index.end:
                        if sindex.isGroup: groups.append(sindex)
                    else: break
                yield index, groups
                if finalized: break
                index = sindex
            else:
                try: index = next(indexes)
                except StopIteration: break
                
    def listInject(self, indexes):
        '''
        Lists the inject indexes.
        
        @param indexes: Iterable(Index)
            The iterable of indexes to search in.
        @return: list[Index]
            The list of inject indexes.
        '''
        assert isinstance(indexes, Iterable), 'Invalid indexes %s' % indexes
        
        inject = []
        for index in indexes:
            assert isinstance(index, Index), 'Invalid index %s' % index
            if index.isInject: inject.append(index)
        return inject
        
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
        assert isinstance(content.source, IInputStreamCT), 'Invalid content source %s' % content.source
        
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
        @param captures: dictionary{string: bytes}
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
        assert isinstance(content.source, IInputStreamCT), 'Invalid content source %s' % content.source
        assert until is None or isinstance(until, int), 'Invalid until offset %s' % until
        
        for inject in injectors:
            assert isinstance(inject, Index), 'Invalid index %s' % inject
            assert inject.isInject, 'Invalid inject %s' % inject
            
            if inject.start >= content.source.tell() and (until is None or inject.end <= until):
                # We provide what is before the inject.
                for bytes in self.extractor(content, inject.start): yield bytes
                self.discard(content, inject.end)  # We just need to remove the content to be injected.
                
                if inject.value is not None and inject.value in captures: yield captures[inject.value]
                
        # We provide the remaining content.
        for bytes in self.extractor(content, until): yield bytes
                
    def capture(self, groups, content):
        '''
        Captures the provided index groups.

        @param groups: list[Index]
            The list of group indexes to capture the values for.
        @param content: Content
            The content to capture from.
        @param current: integer
            The current index in the stream.
        @return: tuple(bytes, dictionary{string: bytes})|None
            A tuple having on the first position the bytes that have been read for the capture and on the second the
            dictionary containing as a key the group value and as a value the captured bytes. Retuens None if ther is
            nothing to capture.
        '''
        assert isinstance(groups, list), 'Invalid groups %s' % groups
        assert groups, 'At least on group index is required %s' % groups
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        assert isinstance(content.source, IInputStreamCT), 'Invalid content source %s' % content.source
        
        egroup = max(groups, key=lambda group: group.end)
        assert isinstance(egroup, Index), 'Invalid index %s' % egroup
        if egroup.end < content.source.tell():
            raise IOError('Invalid stream offset %s, expected a value less then %s' % (content.source.tell(), egroup.end))
        
        nbytes = egroup.end - content.source.tell()
        if nbytes == 0: return
        offset = content.source.tell()
        capture = content.source.read(nbytes)
        
        captures = {}
        for group in groups:
            assert isinstance(group, Index), 'Invalid index %s' % group
            assert group.isGroup, 'Invalid group %s' % group
            captures[group.value] = content.encode(capture[group.start - offset: group.end - offset])

        return content.encode(capture), captures
                
    def discard(self, content, until):
        '''
        Discard from the content source the provided number of bytes.
        
        @param content: Content
            The content to discard from.
        @param until: integer
            The offset until to discard bytes.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(content.source, IInputStreamCT), 'Invalid content source %s' % content.source
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
