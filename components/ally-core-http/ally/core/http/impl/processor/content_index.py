'''
Created on Apr 4, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content index header encoding.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IEncoderHeader
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
    
# --------------------------------------------------------------------

@injected
class ContentIndexEncodeHandler(HandlerProcessorProceed):
    '''
    Implementation for a processor that provides the encoding of the index as a header.
    '''
    
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
        assert isinstance(self.byteOrder, str), 'Invalid byte order %s' % self.byteOrder
        assert isinstance(self.bytesIndexCount, int), 'Invalid bytes index count %s' % self.bytesIndexCount
        assert isinstance(self.bytesOffset, int), 'Invalid bytes offset %s' % self.bytesOffset
        assert isinstance(self.bytesMark, int), 'Invalid bytes mark %s' % self.bytesMark
        assert isinstance(self.bytesValueId, int), 'Invalid bytes value id %s' % self.bytesValueId
        assert isinstance(self.bytesValueSize, int), 'Invalid bytes value size %s' % self.bytesValueSize
        assert isinstance(self.encoding, str), 'Invalid encoding %s' % self.encoding
        super().__init__()

    def process(self, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Encode the index header.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        if response.isSuccess is False: return  # No indexes required for errors.
        if not responseCnt.indexes: return  # There is no index
        assert isinstance(responseCnt.indexes, list), 'Invalid indexes %s' % responseCnt.indexes
        assert isinstance(response.encoderHeader, IEncoderHeader), 'Invalid header encoder %s' % response.encoderHeader
        
        out = BytesIO()
        out.write(len(responseCnt.indexes).to_bytes(self.bytesIndexCount, self.byteOrder))
        current, values = 0, {}
        for index, header in responseCnt.indexes:
            offset = index - current
            current = index
            
            out.write(offset.to_bytes(self.bytesOffset, self.byteOrder))
            if header is None: out.write(int(0).to_bytes(self.bytesMark, self.byteOrder))
            else:
                mark, value = header
                # TODO: temo
                mark = 1
                
                out.write(mark.to_bytes(self.bytesMark, self.byteOrder))
                if value is None: out.write(int(0).to_bytes(self.bytesValueId, self.byteOrder))
                else:
                    assert isinstance(value, str), 'Invalid value %s' % value
                    valueId = values.get(value)
                    if valueId is None: valueId = values[value] = len(values) + 1
                    out.write(valueId.to_bytes(self.bytesValueId, self.byteOrder))
        
        out.write(len(values).to_bytes(self.bytesValueId, self.byteOrder))
        for value, valueId in values.items():
            out.write(valueId.to_bytes(self.bytesValueId, self.byteOrder))
            out.write(len(value).to_bytes(self.bytesValueSize, self.byteOrder))
            out.write(value.encode(self.encoding))
        
        index = str(binascii.b2a_base64(zlib.compress(out.getvalue()))[:-1], self.encoding)
        
        response.encoderHeader.encode(self.nameIndex, index)
