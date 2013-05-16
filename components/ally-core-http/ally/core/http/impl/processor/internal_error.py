'''
Created on Jun 22, 2012

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provide the internal error representation. This is usually when the server fails badly.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.execution import Error
from ally.exception import DevelError
from ally.http.impl.processor.internal_error import InternalErrorHandler, \
    ResponseContent, Response
from ally.http.spec.codes import INTERNAL_ERROR

# --------------------------------------------------------------------

class ResponseDevel(Response):
    '''
    The devel response context.
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)
    errorMessage = defines(str)

# --------------------------------------------------------------------

@injected
class InternalDevelErrorHandler(InternalErrorHandler):
    '''
    Extension for @see: InternalErrorHandler that better handles the DevelError.
    '''
    
    def __init__(self):
        '''
        Construct the internal development error handler.
        '''
        assert isinstance(self.errorHeaders, dict), 'Invalid error headers %s' % self.errorHeaders
        super().__init__(response=ResponseDevel)
    
    def processError(self, error, response, responseCnt, **keyargs):
        '''
        @see: InternalErrorHandler.processError
        
        Handle the error.
        '''
        assert isinstance(error, Error), 'Invalid error execution %s' % error
        assert isinstance(response, ResponseDevel), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        # If there is an explanation for the error occurred, we do not need to make another one
        if ResponseContent.source in responseCnt and responseCnt.source is not None: return

        exc = error.excInfo[1]
        if isinstance(exc, DevelError):
            INTERNAL_ERROR.set(response)
            response.text, response.errorMessage = 'Development error', str(exc)
            if response.headers:
                assert isinstance(response.headers, dict), 'Invalid response headers %s' % response.headers
                response.headers.clear()
            error.retry()  # We try to process now the chain (where it left of) with the exception set.
        else: super().processError(error, response, responseCnt)
