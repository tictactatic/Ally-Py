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
from ally.support.util_io import IInputStream, IClosable
from collections import Callable, Iterable
import logging

# --------------------------------------------------------------------

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
    transcode = requires(Callable)
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
        responseCnt.source = self.assemble(assemblage.requestNode, assemblage.main, assemblage.requestHandler)
        chain.proceed()
        
    # --------------------------------------------------------------------
    
    def assemble(self, node, content, requestHandler):
        '''
        Assembles the content.
        
        @param node: RequestNode
            The request node to assemble based on.
        @param content: Content
            The content to assemble.
        @param requestHandler: callable(url, parameters) -> Content
            The request handler that provides the content for inner requests.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert callable(requestHandler), 'Invalid request handler %s' % requestHandler
        
        current = 0
        for block, sblocks in self.iterBlocks(node, content.indexes):
            assert isinstance(block, Index), 'Invalid block %s' % block
            
            length = block.start - current
            if length > 0:
                # Provide all bytes until start.
                for bytes in self.pull(content.source, length): yield bytes
                
            length = block.end - block.start
            if length > 0:
                # Skip the block bytes.
                for bytes in self.pull(content.source, length): pass
                
            current = block.end
            
        # Providing the remaining bytes.
        for bytes in self.pull(content.source): yield bytes
        
    def iterBlocks(self, node, indexes):
        '''
        Iterates the blocks indexes for the provided node.
        
        @param node: RequestNode
            The request node to iterate the blocks for.
        @param indexes: Iterable(Index)
            The iterable of indexes to search in.
        @return: Iterable(tuple(Index, list[Index]))
            Iterates the tuples containing on the first position the block index and on the second the list
            of sub indexes of the block index.
        '''
        assert isinstance(node, RequestNode), 'Invalid request node %s' % node
        assert isinstance(node.requests, dict), 'Invalid request node requests %s' % node.requests
        assert isinstance(indexes, Iterable), 'Invalid indexes %s' % indexes
        
        #TODO: check '*' in requests
        indexes = iter(indexes)
        try: index = next(indexes)
        except StopIteration: return
        while True:
            assert isinstance(index, Index), 'Invalid index %s' % index
            if index.isBlock and index.value in node.requests:
                sblocks, finalized = [], False
                while True:
                    try: sindex = next(indexes)
                    except StopIteration:
                        finalized = True
                        break
                    assert isinstance(sindex, Index), 'Invalid index %s' % sindex
                    if sindex.end <= index.end: sblocks.append(sindex)
                    else: break
                yield index, sblocks
                if finalized: break
                index = sindex
            else:
                try: index = next(indexes)
                except StopIteration: break
        
    def pull(self, stream, nbytes=None):
        '''
        Pulls from the stream the provided number of bytes.
        
        @param stream: IInputStream
            The stream to pull from.
        @param nbytes: integer|None
            The number of bytes to pull, if None it will pull all remaining bytes
        @return: Iterable(bytes)
            Chunk size bytes pulled from the stream.
        '''
        assert isinstance(stream, IInputStream), 'Invalid stream %s' % stream
        
        if nbytes is None:
            while True:
                block = stream.read(self.maximumBlockSize)
                if block == b'': break
                yield block
        else:
            assert isinstance(nbytes, int), 'Invalid number of bytes %s' % nbytes
            assert nbytes > 0, 'Invalid number of bytes %s' % nbytes
            while nbytes > 0:
                if nbytes <= self.maximumBlockSize: block = stream.read(nbytes)
                else: block = stream.read(self.maximumBlockSize)
                if block == b'': raise IOError('The stream is missing %s bytes' % nbytes)
                nbytes -= len(block)
                yield block
