'''
Created on Apr 4, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content index header encoding.
'''

from ally.container.ioc import injected
from ally.design.cache import CacheWeak
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranchingProceed
from ally.http.spec.server import IEncoderHeader
from io import BytesIO
import binascii
import zlib
from ally.core.spec.transform.index import Index

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

class Mark(Context):
    '''
    The mark context.
    '''
    # ---------------------------------------------------------------- Required
    id = requires(int)
    
class Markers(Context):
    '''
    The indexing markers context.
    '''
    # ---------------------------------------------------------------- Required
    markers = requires(dict)

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
    bytesIndexCount = 3
    # The number of bytes to represent the indexes count.
    bytesOffset = 3
    # The number of bytes to represent the index offset.
    bytesMark = 1
    # The number of bytes to represent the index mark.
    bytesValueId = 2
    # The number of bytes to represent the index values id's.
    bytesValueSize = 1
    # The number of bytes to represent the value size.
    encoding = 'ascii'
    # The string encoding. 

    def __init__(self):
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        assert isinstance(self.nameIndex, str), 'Invalid header name index %s' % self.nameIndex
        assert isinstance(self.byteOrder, str), 'Invalid byte order %s' % self.byteOrder
        assert isinstance(self.bytesIndexCount, int), 'Invalid bytes index count %s' % self.bytesIndexCount
        assert isinstance(self.bytesOffset, int), 'Invalid bytes offset %s' % self.bytesOffset
        assert isinstance(self.bytesMark, int), 'Invalid bytes mark %s' % self.bytesMark
        assert isinstance(self.bytesValueId, int), 'Invalid bytes value id %s' % self.bytesValueId
        assert isinstance(self.bytesValueSize, int), 'Invalid bytes value size %s' % self.bytesValueSize
        assert isinstance(self.encoding, str), 'Invalid encoding %s' % self.encoding
        super().__init__(Branch(self.assembly).using(markers=Markers, Marker=Mark))
        
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
            assert isinstance(chain.arg.markers, Markers), 'Invalid markers %s' % chain.arg.markers
            assert isinstance(chain.arg.markers.markers, dict), 'Invalid markers %s' % chain.arg.markers.markers
            cache.value = chain.arg.markers.markers
        markers = cache.value
        assert isinstance(markers, dict), 'Invalid markers %s' % markers
        
        out = BytesIO()
        out.write(len(responseCnt.indexes).to_bytes(self.bytesIndexCount, self.byteOrder))
        current, values = 0, {}
        for index in responseCnt.indexes:
            assert isinstance(index, Index), 'Invalid index %s' % index
            offset = index.start - current
            current = index.start
            
            assert index.name in markers, 'Invalid mark %s for markers %s' % (index.name, markers)
            marker = markers[index.name]
            assert isinstance(marker, Mark), 'Invalid marker %s' % marker
            assert isinstance(marker.id, int), 'Invalid marker id %s' % marker.id
            
            out.write(marker.id.to_bytes(self.bytesMark, self.byteOrder))
            out.write(offset.to_bytes(self.bytesOffset, self.byteOrder))
            out.write((index.end - index.start).to_bytes(self.bytesOffset, self.byteOrder))
            
            if index.value is None: out.write(int(0).to_bytes(self.bytesValueId, self.byteOrder))
            else:
                assert isinstance(index.value, str), 'Invalid value %s' % index.value
                valueId = values.get(index.value)
                if valueId is None: valueId = values[index.value] = len(values) + 1
                out.write(valueId.to_bytes(self.bytesValueId, self.byteOrder))
        
        out.write(len(values).to_bytes(self.bytesValueId, self.byteOrder))
        for value, valueId in values.items():
            out.write(valueId.to_bytes(self.bytesValueId, self.byteOrder))
            out.write(len(value).to_bytes(self.bytesValueSize, self.byteOrder))
            out.write(value.encode(self.encoding))
        
        index = str(binascii.b2a_base64(zlib.compress(out.getvalue()))[:-1], self.encoding)
        response.encoderHeader.encode(self.nameIndex, index)
        
