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
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import HeadersDefines, CONTENT_LENGTH, \
    TRANSFER_ENCODING, TRANSFER_ENCODING_CHUNKED
from ally.support.util_io import IInputStream, readGenerator
from codecs import ascii_encode
from collections import Iterable, deque

# --------------------------------------------------------------------

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    source = requires(Iterable, IInputStream)

# --------------------------------------------------------------------

@injected
class ChunkedTransferEncodingHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the HTTP chuncked transfer encoding.
    '''

    chunkMark = '%s\r\n'
    # The mark used to represent chunks.
    chunkEnding = '\r\n'
    # The chunck ending.
    maximumChunkSize = 1024
    # The maximum chunck size in bytes, also used in case the source is a stream.

    def __init__(self):
        assert isinstance(self.chunkMark, str), 'Invalid chunk mark %s' % self.chunkMark
        assert isinstance(self.chunkEnding, str), 'Invalid chunk ending %s' % self.chunkEnding
        assert isinstance(self.maximumChunkSize, int), 'Invalid stream chunck size %s' % self.maximumChunkSize
        super().__init__()
        
        self._chunkEndingBytes = ascii_encode(self.chunkEnding)[0]

    def process(self, chain, response:HeadersDefines, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Encodes the content length.
        '''
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        if responseCnt.source is None: return  # No content to chunck.
        CONTENT_LENGTH.remove(response)
        # We make sure that no content length is not on the headers since this will create a conflict.
        
        TRANSFER_ENCODING.put(response, TRANSFER_ENCODING_CHUNKED)
        if isinstance(responseCnt.source, IInputStream):
            responseCnt.source = self.chuncks(readGenerator(responseCnt.source, self.maximumChunkSize))
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
        buffer, size = deque(), 0
        source = iter(source)
        while True:
            try: chunk = next(source)
            except StopIteration:
                if not buffer: break
                chunk = b''.join(buffer)
                buffer.clear()
                size = 0
            else:
                if size < self.maximumChunkSize and len(chunk) < self.maximumChunkSize:
                    buffer.append(chunk)
                    size += len(chunk)
                    continue
            
            if buffer:
                buffer.append(chunk)
                chunk = b''.join(buffer)
                buffer.clear()
                size = 0
                
            yield ascii_encode(self.chunkMark % hex(len(chunk))[2:])[0]
            yield chunk
            yield self._chunkEndingBytes
            
        yield ascii_encode(self.chunkMark % '0')[0]
        yield self._chunkEndingBytes
