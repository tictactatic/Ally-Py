'''
Created on Jul 13, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the definitions based on error code.
'''

from ally.container.ioc import injected
from ally.core.impl.verifier import IVerifier
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
import itertools

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    definitions = requires(list)

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    definitions = requires(list)
    
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    
class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    errorDefinitions = defines(list)
    # ---------------------------------------------------------------- Required
    code = requires(str)
    isSuccess = requires(bool)

# --------------------------------------------------------------------

@injected
class ErrorDefinitionHandler(HandlerProcessor):
    '''
    Provides the definitions based on error code.
    '''

    errors = dict
    # The errors dictionary having as a key the error code and as a value a list of verifiers
    # to be used for invoker definitions.

    def __init__(self):
        assert isinstance(self.errors, dict), 'Invalid errors %s' % self.errors
        if __debug__:
            for code, verifiers in self.errors.items():
                assert isinstance(code, str), 'Invalid code %s' % code
                assert isinstance(verifiers, list), 'Invalid verifiers %s' % verifiers
                for verifier in verifiers: assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
        super().__init__(Invoker=Invoker)

    def process(self, chain, register:Register, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Parse the request object.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        if response.isSuccess is not False: return  # Not in error.
        if not response.code: return
        
        definitions = None
        if request.invoker:
            assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
            if request.invoker.definitions: definitions = request.invoker.definitions
        if register.definitions:
            if definitions is None: definitions = register.definitions
            else: definitions = itertools.chain(definitions, register.definitions)
            
        if definitions is None: return  # No definitions to process.
        
        verifiers = self.errors.get(response.code)
        if not verifiers: return
        
        if response.errorDefinitions is None: response.errorDefinitions = []
        for defin in definitions:
            for verifier in verifiers:
                assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
                if verifier.isValid(defin):
                    response.errorDefinitions.append(defin)
                    break
