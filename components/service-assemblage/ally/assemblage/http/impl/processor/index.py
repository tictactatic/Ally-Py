'''
Created on Apr 5, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexes for the response content.
'''

from ally.assemblage.http.spec.assemblage import Index
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.support.util_io import IInputStream
from io import BytesIO
import binascii
import zlib

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    headers = requires(dict)

class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Required
    markers = requires(dict)

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
class IndexProviderHandler(HandlerProcessorProceed):
    '''
    Provides the index for the content.
    '''
    
    nameIndex = 'Content-Index'
    # The name for the content index header
    byteOrder = 'little'
    # The byte order to use in decode values.
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
    encode = 'ascii'
    # The string encode. 
    
    def __init__(self):
        assert isinstance(self.nameIndex, str), 'Invalid content index name %s' % self.nameIndex
        assert isinstance(self.byteOrder, str), 'Invalid byte order %s' % self.byteOrder
        assert isinstance(self.bytesIndexCount, int), 'Invalid bytes index count %s' % self.bytesIndexCount
        assert isinstance(self.bytesOffset, int), 'Invalid bytes offset %s' % self.bytesOffset
        assert isinstance(self.bytesMark, int), 'Invalid bytes mark %s' % self.bytesMark
        assert isinstance(self.bytesValueId, int), 'Invalid bytes value id %s' % self.bytesValueId
        assert isinstance(self.bytesValueSize, int), 'Invalid bytes value size %s' % self.bytesValueSize
        assert isinstance(self.encode, str), 'Invalid encode %s' % self.encode
        super().__init__()

    def process(self, response:Response, assemblage:Assemblage, content:Content, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provide the index for content.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        assert isinstance(content, Content), 'Invalid content %s' % content
        
        if not response.headers: return  # No headers available.
        if not assemblage.markers: return  # No markers available
        assert isinstance(response.headers, dict), 'Invalid headers %s' % response.headers
        assert isinstance(assemblage.markers, dict), 'Invalid markers %s' % assemblage.markers
        
        value = response.headers.pop(self.nameIndex, None)  # Also making sure not to pass the index header.
        if not value: return  # No content index available for processing.
        assert isinstance(value, str), 'Invalid value %s' % value
        bvalue = value.encode(self.encode)
        bvalue = binascii.a2b_base64(bvalue)
        bvalue = zlib.decompress(bvalue)
        read = BytesIO(bvalue)
        
        count, current, indexes, valuesIds = self.intFrom(read, self.bytesIndexCount), 0, [], []
        while count > 0:
            count -= 1
            
            mark = self.intFrom(read, self.bytesMark)
            current += self.intFrom(read, self.bytesOffset)
            length = self.intFrom(read, self.bytesOffset)
            valueId = self.intFrom(read, self.bytesValueId)
            
            marker = assemblage.markers.get(mark)
            if marker:
                index = Index(marker, current, current + length)
                indexes.append(index)
                valuesIds.append(valueId)
            
        count, values = self.intFrom(read, self.bytesValueId), {}
        while count > 0:
            count -= 1
            valueId = self.intFrom(read, self.bytesValueId)
            countValue = self.intFrom(read, self.bytesValueSize)
            value = read.read(countValue)
            if len(value) != countValue: raise IOError()
            values[valueId] = str(value, self.encode)
            
        for index, valueId in zip(indexes, valuesIds):
            if valueId: index.value = values[valueId]
        
        if content.indexes is None: content.indexes = indexes
        else: content.indexes.extend(indexes)

    # ----------------------------------------------------------------
    
    def intFrom(self, inp, nbytes):
        '''
        Creates the integer value from the provided input stream.
        '''
        assert isinstance(inp, IInputStream), 'Invalid input stream %s' % inp
        assert isinstance(nbytes, int), 'Invalid number of bytes %s' % nbytes
        
        byts = inp.read(nbytes)
        if byts == b'': raise IOError()
        
        return int.from_bytes(byts, self.byteOrder)
