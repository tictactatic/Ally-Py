'''
Created on Aug 9, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the error code conversion to response.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import PATH_NOT_FOUND, CodedHTTP, CodeHTTP
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    parameters = requires(list)

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)
    allows = defines(set)

# --------------------------------------------------------------------

@injected
class ErrorPopulator(HandlerProcessor):
    '''
    Provides the error processor, practically it just populates error data that the other processors can convert to
    a proper response.
    '''
    
    nameStatus = 'status'
    # The status parameter name
    nameAllow = 'allow'
    # The allow header name
    statusToCode = dict
    # The status to code dictionary, the key is the HTTP status and as a value the CodeHTTP to set on response.

    def __init__(self):
        assert isinstance(self.nameStatus, str), 'Invalid name status %s' % self.nameStatus
        assert isinstance(self.nameAllow, str), 'Invalid name allow %s' % self.nameAllow
        assert isinstance(self.statusToCode, dict), 'Invalid status to code %s' % self.statusToCode
        super().__init__()

    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the error data populating.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        if response.isSuccess is False: return  # If the request is already failed no need to place other code
        
        status, allows = None, set()
        for name, value in request.parameters:
            if status is None and name == self.nameStatus:  # If status appears more then once we just use the first one.
                try: status = int(value)
                except ValueError:
                    assert log.debug('Invalid status value \'%s\'', value) or True
            elif name == self.nameAllow: allows.add(value)
        
        code = self.statusToCode.get(status, PATH_NOT_FOUND)
        assert isinstance(code, CodeHTTP), 'Invalid code %s' % code
        code.set(response)
        
        if response.allows is None: response.allows = allows
        else: response.allows.update(allows)
        
