'''
Created on Aug 9, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the method override header handling.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import HEADER_ERROR, CodedHTTP
from ally.http.spec.headers import HeadersRequire, HeaderRaw
from ally.http.spec.server import HTTP_GET, HTTP_POST, HTTP_DELETE, HTTP_PUT
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

METHOD_OVERRIDE = HeaderRaw('X-HTTP-Method-Override')
# The method override header.

# --------------------------------------------------------------------

@injected
class MethodOverrideConfigurations:
    '''
    Provides the method override configurations.
    '''
    
    methodsOverride = {
                       HTTP_GET: [HTTP_DELETE],
                       HTTP_POST: [HTTP_PUT],
                       }
    # A dictionary containing as a key the original method and as a value the methods that are allowed for override.

    def __init__(self):
        assert isinstance(self.methodsOverride, dict), 'Invalid methods override %s' % self.methodsOverride
        if __debug__:
            for method, methods in self.methodsOverride.items():
                assert isinstance(method, str), 'Invalid method name %s' % method
                assert isinstance(methods, list), 'Invalid methods %s' % methods
                for method in methods: assert isinstance(method, str), 'Invalid method name %s' % method
        
# --------------------------------------------------------------------

class Request(HeadersRequire):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    method = requires(str)

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)

# --------------------------------------------------------------------

@injected
class MethodOverrideHandler(HandlerProcessor, MethodOverrideConfigurations):
    '''
    Provides the method override processor.
    '''

    def __init__(self):
        MethodOverrideConfigurations.__init__(self)
        HandlerProcessor.__init__(self)

    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Overrides the request method based on a provided header.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error

        value = METHOD_OVERRIDE.fetch(request)
        if value:
            allowed = self.methodsOverride.get(request.method)
            if not allowed:
                HEADER_ERROR.set(response)
                response.text = 'Cannot override method \'%s\'' % request.method
                return

            value = value.upper()
            if value not in allowed:
                HEADER_ERROR.set(response)
                response.text = 'Cannot override method \'%s\' to method \'%s\'' % (request.method, value)
                return

            assert log.debug('Successfully overridden method %s with %s', request.method, value) or True
            request.method = value

# --------------------------------------------------------------------

class ResponseAllow(Context):
    '''
    The response allow context.
    '''
    # ---------------------------------------------------------------- Required
    allows = requires(set)
    
# --------------------------------------------------------------------

@injected
class MethodOverrideAllowHandler(HandlerProcessor, MethodOverrideConfigurations):
    '''
    Provides the method override allow update processor.
    '''
    
    def __init__(self):
        MethodOverrideConfigurations.__init__(self)
        HandlerProcessor.__init__(self)

    def process(self, chain, response:ResponseAllow, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the allow for method override.
        '''
        assert isinstance(response, ResponseAllow), 'Invalid response %s' % response
        if not response.allows: return  # No allowed methods to process.
        assert isinstance(response.allows, set), 'Invalid allow %s' % response.allow
        
        for method, methods in self.methodsOverride.items():
            if not response.allows.isdisjoint(methods): response.allows.add(method)
