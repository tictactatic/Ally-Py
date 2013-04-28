'''
Created on Apr 4, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content index header encoding.
'''

from ally.container.ioc import injected
from ally.core.spec.transform.index import Index
from ally.design.cache import CacheWeak
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranchingProceed
from ally.http.spec.server import IEncoderHeader
from ally.indexing.spec.model import Block
from io import BytesIO
import binascii
import zlib

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    isSuccess = requires(bool)
    encoderHeader = requires(IEncoderHeader)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    indexes = requires(list)

class Mapping(Context):
    '''
    The index mapping context.
    '''
    # ---------------------------------------------------------------- Required
    blockId = requires(int)
    block = requires(Block)
    
class Blocks(Context):
    '''
    The blocks index context.
    '''
    # ---------------------------------------------------------------- Required
    blocks = requires(dict)

# --------------------------------------------------------------------

@injected
class ContentIndexEncodeHandler(HandlerBranchingProceed):
    '''
    Implementation for a processor that provides the encoding of the index as a header.
    '''
    
    assembly = Assembly
    # The assembly used for processing markers.
    
    nameIndex = 'Content-Index'
    # The name for the content index header
    byteOrder = 'little'
    # The byte order to use in encoding values.
    bytesIndexCount = 1
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
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        assert isinstance(self.nameIndex, str), 'Invalid header name index %s' % self.nameIndex
        assert isinstance(self.byteOrder, str), 'Invalid byte order %s' % self.byteOrder
        assert isinstance(self.bytesIndexCount, int), 'Invalid bytes index count %s' % self.bytesIndexCount
        assert isinstance(self.bytesBlock, int), 'Invalid bytes mark %s' % self.bytesMark
        assert isinstance(self.bytesOffset, int), 'Invalid bytes offset %s' % self.bytesOffset
        assert isinstance(self.bytesValueId, int), 'Invalid bytes value id %s' % self.bytesValueId
        assert isinstance(self.bytesValueSize, int), 'Invalid bytes value size %s' % self.bytesValueSize
        assert isinstance(self.encoding, str), 'Invalid encoding %s' % self.encoding
        super().__init__(Branch(self.assembly).using(blocks=Blocks, Mapping=Mapping))
        
        self._cache = CacheWeak()

    def process(self, processing, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Encode the index header.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        if response.isSuccess is False: return  # No indexes required for errors.
        if not responseCnt.indexes: return  # There is no index
        assert isinstance(responseCnt.indexes, list), 'Invalid indexes %s' % responseCnt.indexes
        assert isinstance(response.encoderHeader, IEncoderHeader), 'Invalid header encoder %s' % response.encoderHeader
        
        cache = self._cache.key(processing)
        if not cache.has:
            chain = Chain(processing)
            chain.process(**processing.fillIn()).doAll()
            assert isinstance(chain.arg.blocks, Blocks), 'Invalid blocks %s' % chain.arg.blocks
            assert isinstance(chain.arg.blocks.blocks, dict), 'Invalid blocks %s' % chain.arg.blocks.blocks
            cache.value = chain.arg.blocks.blocks
        blocks = cache.value
        assert isinstance(blocks, dict), 'Invalid blocks %s' % blocks
        
        out = BytesIO()
        out.write(len(responseCnt.indexes).to_bytes(self.bytesIndexCount, self.byteOrder))
        values = {}
        for index in responseCnt.indexes:
            assert isinstance(index, Index), 'Invalid index %s' % index
            assert index.block in blocks, 'Unknown block \'%s\' in definitions %s' % (index.block, list(blocks))
            mapping = blocks[index.block]
            assert isinstance(mapping, Mapping), 'Invalid mapping %s' % mapping
            assert isinstance(mapping.block, Block), 'Invalid mapping block %s' % mapping.block
           
            out.write(mapping.blockId.to_bytes(self.bytesBlock, self.byteOrder))
            for key in mapping.block.keys:
                assert key in index.values, 'Missing key value for %s' % key
                value = index.values.get(key)
                valueId = values.get(value)
                if valueId is None: valueId = values[value] = len(values) + 1
                out.write(valueId.to_bytes(self.bytesValueId, self.byteOrder))
                
            for name in mapping.block.indexes:
                assert name in index.values, 'Missing index value \'%s\' for \'%s\'' % (name, index.block)
                out.write(index.values[name].to_bytes(self.bytesOffset, self.byteOrder))
        
        out.write(len(values).to_bytes(self.bytesValueId, self.byteOrder))
        for name, valueId in values.items():
            out.write(valueId.to_bytes(self.bytesValueId, self.byteOrder))
            out.write(len(name).to_bytes(self.bytesValueSize, self.byteOrder))
            out.write(name.encode(self.encoding))
        
        index = str(binascii.b2a_base64(zlib.compress(out.getvalue()))[:-1], self.encoding)
        response.encoderHeader.encode(self.nameIndex, index)
        
