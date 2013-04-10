'''
Created on Apr 10, 2013

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the chunked transfer encoding.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IEncoderHeader
from ally.support.util_io import IInputStream, readGenerator
from codecs import ascii_encode
from collections import Iterable

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    headers = requires(dict)
    encoderHeader = requires(IEncoderHeader)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    source = requires(Iterable, IInputStream)

# --------------------------------------------------------------------

@injected
class ChunkedTransferEncodingHandler(HandlerProcessorProceed):
    '''
    Implementation for a processor that provides the HTTP chuncked transfer encoding.
    '''
    
    nameTransferEncoding = 'Transfer-Encoding'
    # The name for the chunked transfer encoding header.
    valueChunked = 'chunked'
    # The chunked value to place on the transfer encoding header.
    nameContentLength = 'Content-Length'
    # The name of the content length header
    chunkMark = '%s\r\n'
    # The mark used to represent chunks.
    chunkEnding = '\r\n'
    # The chunck ending.
    streamChunkSize = 1024
    # The chunck size in bytes used in case the source is a stream.

    def __init__(self):
        assert isinstance(self.nameTransferEncoding, str), 'Invalid transfer encoding name %s' % self.nameTransferEncoding
        assert isinstance(self.valueChunked, str), 'Invalid chunked value %s' % self.valueChunked
        assert isinstance(self.nameContentLength, str), 'Invalid content length name %s' % self.nameContentLength
        assert isinstance(self.chunkMark, str), 'Invalid chunk mark %s' % self.chunkMark
        assert isinstance(self.chunkEnding, str), 'Invalid chunk ending %s' % self.chunkEnding
        assert isinstance(self.streamChunkSize, int), 'Invalid stream chunck size %s' % self.streamChunkSize
        super().__init__()
        
        self._chunkEndingBytes = ascii_encode(self.chunkEnding)[0]

    def process(self, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Encodes the content length.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        assert isinstance(response.encoderHeader, IEncoderHeader), \
        'Invalid response header encoder %s' % response.encoderHeader
        
        if responseCnt.source is None: return  # No content to chunck.
        
        response.encoderHeader.encode(self.nameTransferEncoding, self.valueChunked)
        if response.headers:
            assert isinstance(response.headers, dict), 'Invalid headers %s' % response.headers
            response.headers.pop(self.nameContentLength, None)
            # We make sure that no content length is not on the headers since this will create a conflict.
                
        if isinstance(responseCnt.source, IInputStream):
            responseCnt.source = self.chuncks(readGenerator(responseCnt.source, self.streamChunkSize))
        else:
            assert isinstance(responseCnt.source, Iterable), 'Invalid source %s' % responseCnt.source
            responseCnt.source = self.chuncks(responseCnt.source)
    
    # --------------------------------------------------------------------
    
    def chuncks(self, source):
        '''
        Provides the chuncks.
        
        @param source: Iterable(bytes)
            The source to stream chuncks for.
        @return: Iterable(bytes)
            The transfer chuncks.
        '''
        assert isinstance(source, Iterable), 'Invalid source %s' % source
        for chunk in source:
            yield ascii_encode(self.chunkMark % hex(len(chunk))[2:])[0]
            yield chunk
            yield self._chunkEndingBytes
        yield ascii_encode(self.chunkMark % '0')[0]
        yield self._chunkEndingBytes
