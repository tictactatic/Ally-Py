'''
Created on Jun 22, 2012

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provide the internal error representation. This is usually when the server fails badly.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Error
from ally.design.processor.handler import Handler
from ally.design.processor.processor import Processor
from ally.http.spec.codes import INTERNAL_ERROR, CodedHTTP
from ally.support.util_io import convertToBytes, IInputStream
from collections import Iterable
from io import StringIO, BytesIO
import logging
import traceback

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    headers = defines(dict)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Optional
    source = defines(IInputStream, Iterable)

# --------------------------------------------------------------------

@injected
class InternalErrorHandler(Handler):
    '''
    Implementation for a processor that provides the handling of internal errors.
    '''

    errorHeaders = {'Content-Type':'text;charset=UTF-8'}
    # The headers that will be placed on the response.

    def __init__(self, response=Response, responseCnt=ResponseContent, **contexts):
        '''
        Construct the internal error handler.
        '''
        assert isinstance(self.errorHeaders, dict), 'Invalid error headers %s' % self.errorHeaders
        super().__init__(Processor(dict(response=Response, responseCnt=ResponseContent, **contexts), self.process))

    def process(self, chain, **keyargs):
        '''
        Provides the additional arguments by type to be populated.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        chain.onError(self.processError)
        if __debug__:
            # If in debug mode and the response content has a source generator then we will try to read that
            # in order to catch any exception before the actual streaming.
            chain.onFinalize(self.processFinalization)
            
    def processFinalization(self, final, response, responseCnt, **keyargs):
        '''
        Process the finalization.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        if isinstance(responseCnt.source, Iterable):
            content = BytesIO()
            try:
                for bytes in responseCnt.source: content.write(bytes)
            except:
                log.exception('Exception occurred while processing the content')
                error = StringIO()
                traceback.print_exc(file=error)
                INTERNAL_ERROR.set(response)
                response.headers = dict(self.errorHeaders)
                responseCnt.source = convertToBytes(self.errorResponse(error), 'UTF-8', 'backslashreplace')
            else:
                content.seek(0)
                responseCnt.source = content
            
    def processError(self, error, response, responseCnt, **keyargs):
        '''
        Process the error.
        '''
        assert isinstance(error, Error), 'Invalid error execution %s' % error
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        # If there is an explanation for the error occurred, we do not need to make another one
        if responseCnt.source is not None: return
        
        ferror = StringIO()
        traceback.print_exception(*error.excInfo, file=ferror)
        INTERNAL_ERROR.set(response)
        response.headers = dict(self.errorHeaders)
        responseCnt.source = convertToBytes(self.errorResponse(ferror), 'UTF-8', 'backslashreplace')

    def errorResponse(self, error):
        '''
        Generates the error response.
        
        @param error: StringIO
            The error stream that contains the stack info.
        '''
        assert isinstance(error, IInputStream), 'Invalid error stream %s' % error

        yield 'Internal server error occurred, this is a major issue so please contact your administrator\n\n'
        error.seek(0)
        yield error.read()
        
