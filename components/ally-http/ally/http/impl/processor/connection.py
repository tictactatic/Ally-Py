'''
Created on Apr 10, 2013

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provide the ensures that the connection is set on closed, this is needed for HTTP/1.1 protocol.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler
from ally.design.processor.processor import Processor
from ally.http.spec.headers import CONNECTION, CONNECTION_CLOSE, HeadersRequire, \
    CONNECTION_KEEP, HeadersDefines, CONTENT_LENGTH
from ally.support.util_io import IInputStream
from collections import Iterable

# --------------------------------------------------------------------

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Optional
    source = optional(IInputStream, Iterable)
    
# --------------------------------------------------------------------

@injected
class ConnectionHandler(Handler):
    '''
    Implementation for a processor that ensures the connection header set, this is needed for HTTP/1.1 protocol.
    '''

    def __init__(self):
        super().__init__(Processor({}, self.process))
        
    def process(self, chain, request:HeadersRequire, response:HeadersDefines, responseCnt:ResponseContent, **keyargs):
        '''
        Ensure the response content length at the end of the chain execution.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        if (CONNECTION.fetch(request) or '').lower() == CONNECTION_KEEP: chain.onFinalize(processKeep)
        else: chain.onFinalize(processClosed)
        
# --------------------------------------------------------------------

@injected
class ConnectionCloseHandler(Handler):
    '''
    Implementation for a processor that ensures the connection is set on closed, this is needed for HTTP/1.1 protocol.
    '''

    def __init__(self):
        super().__init__(Processor({}, self.process))
        
    def process(self, chain, **keyargs):
        '''
        Ensure the response content length at the end of the chain execution.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        chain.onFinalize(processClosed)

# --------------------------------------------------------------------

def processKeep(final, response, responseCnt, **keyargs):
    '''
    Puts the keep connection header.
    '''
    assert isinstance(response, HeadersDefines), 'Invalid response %s' % response
    
    if CONTENT_LENGTH.has(response):
        CONNECTION.put(response, CONNECTION_KEEP)
        return
    if ResponseContent.source in responseCnt and responseCnt.source is None:
        CONTENT_LENGTH.put(response, '0')
        CONNECTION.put(response, CONNECTION_KEEP)
        return
    
    CONNECTION.put(response, CONNECTION_CLOSE)
    
def processClosed(final, response, **keyargs):
    '''
    Puts the closed connection header.
    '''
    assert isinstance(response, HeadersDefines), 'Invalid response %s' % response
    CONNECTION.put(response, CONNECTION_CLOSE)
