'''
Created on Jan 5, 2012

@package: ally core sql alchemy
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides support for SQL alchemy a processor for automatic session handling.
'''

from ally.api.config import DELETE
from ally.api.error import InputError, IdError
from ally.core.spec.codes import INPUT_ERROR, Coded
from ally.design.processor.attribute import optional, defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Error
from ally.design.processor.handler import HandlerProcessor
from ally.internationalization import _
from ally.support.sqlalchemy.session import rollback, commit, setKeepAlive, \
    endSessions
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    method = requires(int)
        
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    
class Response(Coded):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    errorInput = defines(InputError, doc='''
    @rtype: InputError
    The input error translated from SQL alchemy error.
    ''')
    # ---------------------------------------------------------------- Optional
    isSuccess = optional(bool)

# --------------------------------------------------------------------

class TransactionWrappingHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the SQLAlchemy session handling.
    '''
    
    def __init__(self):
        super().__init__(request=Request, Invoker=Invoker)

    def process(self, chain, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Wraps the invoking and all processors after invoking in a transaction.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(response, Response), 'Invalid response %s' % response

        setKeepAlive(True)
        chain.onError(self.processError)
        chain.onFinalize(self.processEnd)
    
    def processError(self, error, request, response, **keyargs):
        '''
        Process the transaction error.
        '''
        assert isinstance(error, Error), 'Invalid error %s' % error
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(error.exception, Exception), 'Invalid error exception %s' % error.exception
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        
        exc = None
        if isinstance(error.exception, NoResultFound): exc = IdError()
        elif isinstance(error.exception, IntegrityError):
            exc = InputError(_('There is already an entity having this unique properties'))
        elif isinstance(error.exception, OperationalError):
            if request.invoker.method == DELETE: exc = InputError(_('Cannot delete because is used'))
            else: exc = InputError(_('An entity relation identifier is not valid'))
            
        if exc is not None:
            INPUT_ERROR.set(response)
            exc.with_traceback(error.exception.__traceback__)
            response.errorInput = exc
            error.retry()
    
    def processEnd(self, final, response, **keyargs):
        '''
        Process the end of the transaction.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        if Response.isSuccess in response:
            if response.isSuccess is True: endSessions(commit)
            else: endSessions(rollback)
        else: endSessions(commit)  # Commit if there is no success flag
            
