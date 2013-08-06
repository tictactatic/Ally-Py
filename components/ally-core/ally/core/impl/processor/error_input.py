'''
Created on Aug 2, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the input error handling handler.
'''


from ally.api.error import InputError
from ally.core.impl.processor.base import ErrorResponse, addError
from ally.design.processor.attribute import requires
from ally.design.processor.handler import HandlerProcessor
from ally.design.processor.context import Context
from ally.api.operator.type import TypeModel, TypeProperty
from ally.api.config import GET, INSERT, DELETE, UPDATE
from ally.api.type import Input

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    method = requires(int)
    inputs = requires(tuple)
    target = requires(TypeModel)
        
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    
class Response(ErrorResponse):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    errorInput = requires(InputError)

# --------------------------------------------------------------------

class ErrorInputHandler(HandlerProcessor):
    '''
    Implementation for a processor that input error handling handler.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker)

    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the input error handling.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if response.isSuccess is not False: return  # Skip in case the response is not in error
        if response.errorInput is None: return  # No input error to handle.
        assert isinstance(response.errorInput, InputError), 'Invalid input error %s' % response.errorInput
        
        if response.errorInput.messages:
            if request.invoker:
                assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
                bindType = None
                if request.invoker.method == GET:
                    for inp in request.invoker.inputs:
                        assert isinstance(inp, Input), 'Invalid input %s' % inp
                        if isinstance(inp.type, TypeProperty) and inp.type.parent == request.invoker.target:
                            assert isinstance(inp.type, TypeProperty)
                            bindType = inp.type
                elif request.invoker.method == INSERT or request.invoker.method == UPDATE:
                    bindType = request.invoker.target
                elif request.invoker.method == DELETE:
                    for inp in request.invoker.inputs:
                        assert isinstance(inp, Input), 'Invalid input %s' % inp
                        if isinstance(inp.type, TypeProperty): bindType = inp.type
                
                if bindType:
                    response.errorInput.messageByType[bindType] = response.errorInput.messages
                    response.errorInput.messages = []
        
        addError(response, str(response.errorInput))
