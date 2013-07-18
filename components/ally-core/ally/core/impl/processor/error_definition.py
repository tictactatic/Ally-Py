'''
Created on Jul 13, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the definitions based on error code.
'''

from ally.container.ioc import injected
from ally.core.impl.processor.base import addError
from ally.core.spec.definition import IVerifier
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
import itertools
from ally.design.processor.resolvers import resolversFor

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
    errorMessages = defines(list)
    # ---------------------------------------------------------------- Required
    code = requires(str)
    isSuccess = requires(bool)

# --------------------------------------------------------------------

@injected
class ErrorDefinitionHandler(HandlerProcessor):
    '''
    Provides the definitions based on error code.
    '''

    errors = list
    # The errors list containing tuples having as the first value the error code, as the second the verifier
    # to be used for invoker definitions, and on third the messages to be added also if the verifiers check at least one
    # definition.

    def __init__(self):
        assert isinstance(self.errors, list), 'Invalid errors %s' % self.list
        
        resolvers = resolversFor(dict(Invoker=Invoker))
        for code, verifier, messages in self.errors:
            assert isinstance(code, str), 'Invalid code %s' % code
            assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
            assert isinstance(messages, tuple), 'Invalid messages %s' % messages
            for message in messages: assert isinstance(message, str), 'Invalid message %s' % message
            verifier.prepare(resolvers)
            
        super().__init__(**resolvers)

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
        
        for code, verifier, messages in self.errors:
            if code != response.code: continue
            
            verified, unverified = [], []
            for defin in definitions:
                assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
                if verifier.isValid(defin): verified.append(defin)
                else: unverified.append(defin)
            
            if verified: addError(response, messages, verified)
            definitions = unverified
