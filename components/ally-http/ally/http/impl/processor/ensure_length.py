'''
Created on Apr 10, 2013

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provide the ensures for the content length on the response, this is needed for HTTP/1.1 protocol.
'''

from ally.container.ioc import injected
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler
from ally.design.processor.processor import Processor
from ally.http.spec.server import ResponseHTTP, ResponseContentHTTP
from ally.support.util_io import IInputStream, pipe
from collections import Iterable
from functools import partial
from io import BytesIO

# --------------------------------------------------------------------

@injected
class EnsureLengthHandler(Handler):
    '''
    Implementation for a processor that ensures for the content length on the response, this is needed for HTTP/1.1 protocol.
    '''

    nameContentLength = 'Content-Length'
    # The name of the content length header
    names = ['Transfer-Encoding']
    # The additional header names that if present will prevent the length processing.

    def __init__(self):
        '''
        Construct the internal error handler.
        '''
        assert isinstance(self.nameContentLength, str), 'Invalid content length name %s' % self.nameContentLength
        assert isinstance(self.names, list), 'Invalid names %s' % self.names
        super().__init__(Processor({}, self.process))
        
        self._names = set(self.nameContentLength.lower())
        for name in self.names:
            assert isinstance(name, str), 'Invalid header name %s' % name
            self._names.add(name.lower())

    def process(self, chain, **keyargs):
        '''
        Ensure the response content length at the end of the chain execution.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        callBack = partial(self.processLength, chain)
        chain.callBackError(callBack)
        chain.callBack(callBack)
        
    # --------------------------------------------------------------------
    
    def processLength(self, chain):
        '''
        Process the length for the chain responses.
        
        @param chain: Chain
            The chain to process the responses on.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        response, responseCnt = chain.arg.response, chain.arg.responseCnt
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        assert ResponseHTTP.headers in response, 'Invalid response %s with no headers' % response

        if response.headers:
            assert isinstance(response.headers, dict), 'Invalid response headers %s' % response.headers
            for name in response.headers:
                assert isinstance(name, str), 'Invalid name %s' % name
                if name.lower() in self._names: return  # There is a content length or content headers specified.
        else:
            response.headers = {}
            
        if ResponseContentHTTP.source in responseCnt and responseCnt.source is not None:
            content = BytesIO()
            if isinstance(responseCnt.source, IInputStream): pipe(responseCnt.source, content)
            else:
                assert isinstance(responseCnt.source, Iterable), 'Invalid response content source %s' % responseCnt.source
                for bytes in responseCnt.source: content.write(bytes)
                
            response.headers[self.nameContentLength] = str(content.tell())
            content.seek(0)
            responseCnt.source = content
                
        else: response.headers[self.nameContentLength] = '0'
