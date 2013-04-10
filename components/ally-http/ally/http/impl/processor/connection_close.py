'''
Created on Apr 10, 2013

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provide the ensures that the connection is set on closed, this is needed for HTTP/1.1 protocol.
'''

from ally.container.ioc import injected
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler
from ally.design.processor.processor import Processor
from ally.http.spec.server import ResponseHTTP
from functools import partial

# --------------------------------------------------------------------

@injected
class ConnectionCloseHandler(Handler):
    '''
    Implementation for a processor that ensures the connection is set on closed, this is needed for HTTP/1.1 protocol.
    '''

    nameConnection = 'Connection'
    # The name of the connection header
    valueClose = 'close'
    # The value close to set on the connection header

    def __init__(self):
        '''
        Construct the internal error handler.
        '''
        assert isinstance(self.nameConnection, str), 'Invalid connection name %s' % self.nameConnection
        assert isinstance(self.valueClose, str), 'Invalid close value %s' % self.valueClose
        super().__init__(Processor({}, self.process))
        
        self._nameConnection = self.nameConnection.lower()
        
    def process(self, chain, **keyargs):
        '''
        Ensure the response content length at the end of the chain execution.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        callBack = partial(self.placeConnectionClosed, chain)
        chain.callBackError(callBack)
        chain.callBack(callBack)
        
    # --------------------------------------------------------------------
    
    def placeConnectionClosed(self, chain):
        '''
        Puts the closed connection header.
        
        @param chain: Chain
            The chain to process the header on.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        response = chain.arg.response
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert ResponseHTTP.headers in response, 'Invalid response %s with no headers' % response

        if response.headers:
            assert isinstance(response.headers, dict), 'Invalid response headers %s' % response.headers
            response.headers = {name: value for name, value in response.headers.items() if name.lower() != self._nameConnection}
        else:
            response.headers = {}
        
        response.headers[self.nameConnection] = self.valueClose
