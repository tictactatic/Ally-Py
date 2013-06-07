'''
Created on May 31, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the scheme as an argument for invoked functions.
'''

from ally.api.type import Scheme, Input, typeFor
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import CodedHTTP

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    hasScheme = requires(bool)

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    arguments = defines(dict)
    # ---------------------------------------------------------------- Required
    scheme = requires(str)
    invoker = requires(Context)

class RegisterAssembler(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class InvokerAssembler(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    hasScheme = defines(bool, doc='''
    @rtype: boolean
    Flag indicating that a scheme argument is required for invoker.
    ''')
    solved = defines(set)
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)
    
# --------------------------------------------------------------------

class SchemeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the scheme for invokers when is required.
    '''

    def __init__(self):
        super().__init__(Invoker=Invoker)
        
        self.schemeType = typeFor(Scheme)

    def process(self, chain, request:Request, response:CodedHTTP, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the scheme if required.
        '''
        assert isinstance(request, Request), 'Invalid required request %s' % request
        assert isinstance(response, CodedHTTP), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error
        if request.invoker is None: return  # No invoker to provide the scheme for
        
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        if not request.invoker.hasScheme: return  # No scheme required
        
        if request.arguments is None: request.arguments = {}
        request.arguments[self.schemeType] = request.scheme

# --------------------------------------------------------------------
 
class AssemblerSchemeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides on the assembly the requirement for a scheme argument.
    '''

    def __init__(self):
        super().__init__(Invoker=InvokerAssembler)
        
        self.schemeType = typeFor(Scheme)

    def process(self, chain, register:RegisterAssembler, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the scheme flag if required.
        '''
        assert isinstance(register, RegisterAssembler), 'Invalid register %s' % register
        if not register.invokers: return  # No invokers to process.
        
        for invoker in register.invokers:
            assert isinstance(invoker, InvokerAssembler), 'Invalid invoker %s' % invoker
            if not invoker.inputs: continue
            
            for inp in invoker.inputs:
                assert isinstance(inp, Input), 'Invalid input %s' % inp
                if inp.type == self.schemeType:
                    if invoker.solved is None: invoker.solved = set()
                    invoker.solved.add(inp.name)
                    invoker.hasScheme = True
                    break
                    
