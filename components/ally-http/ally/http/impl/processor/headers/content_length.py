'''
Created on Jun 11, 2012

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the decoding/encoding for the content length header.
'''

from ally.container.ioc import injected
from ally.http.spec.codes import CONTENT_LENGHT_ERROR
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import HeadersRequire, CONTENT_LENGTH, \
    HeadersDefines
from ally.support.util_io import IInputStream, IClosable
from ally.http.spec.codes import CodedHTTP

# --------------------------------------------------------------------

class RequestContentDecode(Context):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Optional
    source = optional(IInputStream)
    # ---------------------------------------------------------------- Defined
    length = defines(int, doc='''
    @rtype: integer
    The content source length in bytes. 
    ''')

class ResponseDecode(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)

# --------------------------------------------------------------------

@injected
class ContentLengthDecodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the decoding of content length HTTP response header.
    '''

    def process(self, chain, request:HeadersRequire, requestCnt:RequestContentDecode, response:ResponseDecode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Decodes the request content length also wraps the content source if is the case.
        '''
        assert isinstance(requestCnt, RequestContentDecode), 'Invalid request content %s' % requestCnt
        assert isinstance(response, ResponseDecode), 'Invalid response %s' % response

        value = CONTENT_LENGTH.fetch(request)
        if value:
            try: requestCnt.length = int(value)
            except ValueError:
                requestCnt.length = None
                if response.isSuccess is False: return  # Skip in case the response is in error
                CONTENT_LENGHT_ERROR.set(response)
                response.text = 'Invalid value \'%s\' for header \'%s\''\
                ', expected an integer value' % (value, self.nameContentLength)
        
        if RequestContentDecode.source in requestCnt and requestCnt.source is not None:
            if requestCnt.length: requestCnt.source = StreamLimitedLength(requestCnt.source, requestCnt.length)
            else:
                requestCnt.source.close()
                requestCnt.source = None  # We do not allow the source without length specified.
                    

class StreamLimitedLength(IInputStream, IClosable):
    '''
    Provides a class that implements the @see: IInputStream that limits the reading from another stream based on the
    provided length.
    '''
    __slots__ = ('_stream', '_length', '_closed', '_offset')

    def __init__(self, stream, length):
        '''
        Constructs the length limited stream.
        
        @param stream: IStream
            The stream to wrap and provide limited reading from.
        @param length: integer
            The number of bytes to allow the read from the wrapped stream.
        '''
        assert isinstance(stream, IInputStream), 'Invalid stream %s' % stream
        assert isinstance(length, int), 'Invalid length %s' % length

        self._stream = stream
        self._length = length
        self._closed = False
        self._offset = 0

    def read(self, nbytes=None):
        '''
        @see: IInputStream.read
        '''
        if self._closed: raise ValueError('I/O operation on a closed content file')
        count = nbytes
        if self._length is not None:
            if self._offset >= self._length:
                return b''
            delta = self._length - self._offset
            if count is None:
                count = delta
            elif count > delta:
                count = delta
        bytes = self._stream.read(count)
        self._offset += len(bytes)
        return bytes

    def close(self):
        '''
        @see: IClosable.close
        '''
        self._closed = True

# --------------------------------------------------------------------

class ResponseContentEncode(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    length = requires(int)

# --------------------------------------------------------------------

@injected
class ContentLengthEncodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the encoding of content length HTTP response header.
    '''

    def process(self, chain, response:HeadersDefines, responseCnt:ResponseContentEncode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Encodes the content length.
        '''
        assert isinstance(responseCnt, ResponseContentEncode), 'Invalid response content %s' % responseCnt

        if responseCnt.length is not None: CONTENT_LENGTH.put(response, str(responseCnt.length))
