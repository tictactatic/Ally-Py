'''
Created on Apr 5, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexes for the response content.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import HeadersRequire, CONTENT_INDEX
from ally.indexing.spec.model import Block
from ally.indexing.spec.modifier import Index
from ally.support.util_io import IInputStream
from collections import Callable
from io import BytesIO
import binascii
import zlib
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Required
    provider = requires(Callable)

class Content(Context):
    '''
    The assemblage content context.
    '''
    # ---------------------------------------------------------------- Defined
    indexes = defines(list, doc='''
    @rtype: list[Index]
    The list of indexes for the response content.
    ''')
    
# --------------------------------------------------------------------

@injected
class IndexProviderHandler(HandlerProcessor):
    '''
    Provides the index for the content.
    '''
    
    byteOrder = 'little'
    # The byte order to use in encoding values.
    bytesIndexCount = 3
    # The number of bytes to represent the indexes count.
    bytesBlock = 1
    # The number of bytes to represent the index block id.
    bytesOffset = 3
    # The number of bytes to represent the index offset.
    bytesValueId = 1
    # The number of bytes to represent the index value id's.
    bytesValueSize = 1
    # The number of bytes to represent the value size.
    encoding = 'ascii'
    # The string encoding. 
    
    def __init__(self):
        assert isinstance(self.byteOrder, str), 'Invalid byte order %s' % self.byteOrder
        assert isinstance(self.bytesIndexCount, int), 'Invalid bytes index count %s' % self.bytesIndexCount
        assert isinstance(self.bytesBlock, int), 'Invalid bytes mark %s' % self.bytesMark
        assert isinstance(self.bytesOffset, int), 'Invalid bytes offset %s' % self.bytesOffset
        assert isinstance(self.bytesValueId, int), 'Invalid bytes value id %s' % self.bytesValueId
        assert isinstance(self.bytesValueSize, int), 'Invalid bytes value size %s' % self.bytesValueSize
        assert isinstance(self.encoding, str), 'Invalid encoding %s' % self.encoding
        super().__init__()

    def process(self, chain, response:HeadersRequire, assemblage:Assemblage, content:Content, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the index for content.
        '''
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        assert isinstance(content, Content), 'Invalid content %s' % content
        
        if not response.headers: return  # No headers available.
        if not assemblage.provider: return  # No blocks provider available
        assert callable(assemblage.provider), 'Invalid blocks provider %s' % assemblage.provider
        
        value = CONTENT_INDEX.fetchOnce(response)
        if not value: return  # No content index available for processing.
        assert isinstance(value, str), 'Invalid value %s' % value
        bvalue = value.encode(self.encoding)
        bvalue = binascii.a2b_base64(bvalue)
        bvalue = zlib.decompress(bvalue)
        read = BytesIO(bvalue)
        
        count, indexes = self._int(read, self.bytesIndexCount), []
        while count > 0:
            count -= 1
            
            blockId = self._int(read, self.bytesBlock)
            block = assemblage.provider(blockId)
            if block is None:
                log.error('Cannot get a block for id %s' % blockId)
                return
            assert isinstance(block, Block), 'Invalid block %s' % block
            
            index = Index(block)
            indexes.append(index)
            
            for key in block.keys:
                index.values[key] = self._int(read, self.bytesValueId)
                
            for name in block.indexes:
                index.values[name] = self._int(read, self.bytesOffset)
                
        count, values = self._int(read, self.bytesValueId), {}
        while count > 0:
            count -= 1
            valueId = self._int(read, self.bytesValueId)
            length = self._int(read, self.bytesValueSize)
            value = read.read(length)
            if len(value) != length: raise IOError('Missing bytes')
            values[valueId] = str(value, self.encoding)
            
        for index in indexes:
            for key in index.block.keys:
                index.values[key] = values[index.values[key]]
        
        if content.indexes is None: content.indexes = indexes
        else: content.indexes.extend(indexes)

    # ----------------------------------------------------------------
    
    def _int(self, inp, nbytes):
        '''
        Creates the integer value from the provided input stream.
        '''
        assert isinstance(inp, IInputStream), 'Invalid input stream %s' % inp
        assert isinstance(nbytes, int), 'Invalid number of bytes %s' % nbytes
        
        byts = inp.read(nbytes)
        if byts == b'': raise IOError()
        
        return int.from_bytes(byts, self.byteOrder)
