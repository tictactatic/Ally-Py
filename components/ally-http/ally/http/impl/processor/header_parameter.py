'''
Created on Apr 29, 2013

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Pushes parameters as header values.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import PARAMETERS_AS_HEADERS, encode, HeadersRequire
from ally.support.http.request import RequesterOptions
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(HeadersRequire):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    parameters = requires(list)

# --------------------------------------------------------------------

@injected
class HeaderParameterHandler(HandlerProcessor):
    '''
    Pushes parameters as header values.
    '''
    
    parameters = list
    # The parameter names to have the values pushed as header values.

    def __init__(self):
        assert isinstance(self.parameters, list), 'Invalid parameters %s' % self.parameters
        if __debug__:
            for name in self.parameters: assert isinstance(name, str), 'Invalid parameter name %s' % name
        super().__init__()

    def process(self, chain, request:Request, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populates parameters as header values.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        if request.parameters: pushHeaders(request, request.parameters, self.parameters)

# --------------------------------------------------------------------

class RequestOptions(Request):
    '''
    The request options context.
    '''
    # ---------------------------------------------------------------- Required
    uri = requires(str)
    
# --------------------------------------------------------------------

@injected
class HeaderParameterOptionsHandler(HandlerProcessor):
    '''
    Implementation for a handler that pushes parameters as header values based on the OPTIONS specifications, the
    request URI is used for getting the options.
    '''
    
    requesterOptions = RequesterOptions
    # The request options used for getting the header options.
    
    def __init__(self):
        assert isinstance(self.requesterOptions, RequesterOptions), \
        'Invalid requester options %s' % self.requesterOptions
        super().__init__()
        
    def process(self, chain, request:RequestOptions, **keyargs):
        '''
        @see: HandlerProcessor.process
        '''
        assert isinstance(request, RequestOptions), 'Invalid request %s' % request
        if not request.parameters: return  # No parameters available.
        
        options = self.requesterOptions.request(request.uri)
        if options:
            assert log.debug('No OPTIONS available at: %s', request.uri) or True
            parametersHeaders = PARAMETERS_AS_HEADERS.decode(options)
            if parametersHeaders: pushHeaders(request, request.parameters, parametersHeaders)
            
# --------------------------------------------------------------------

def pushHeaders(headers, parameters, names):
    '''
    Populates parameters as header values.
    '''
    assert isinstance(parameters, list), 'Invalid parameters %s' % parameters
    assert isinstance(names, list), 'Invalid names %s' % names
    
    for hname in names:
        assert isinstance(hname, str), 'Invalid name %s' % hname
        name = hname.lower()
        value, k = [], 0
        while k < len(parameters):
            if parameters[k][0].lower() == name:
                value.append(parameters[k][1])
                del parameters[k]
                k -= 1
            k += 1
        if value: encode(headers, hname, *value)
