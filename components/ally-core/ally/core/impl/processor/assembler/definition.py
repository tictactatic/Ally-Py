'''
Created on Jul 13, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the definitions info merge with the solicitation and invoker info.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import optional, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Optional
    info = optional(dict)
    # ---------------------------------------------------------------- Required
    definitions = requires(list)

class Solicitation(Context):
    '''
    The solicitation context.
    '''
    # ---------------------------------------------------------------- Optional
    invoker = optional(Context)
    solicitation = optional(Context)
    info = optional(dict)

class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    solicitation = optional(Context)
    info = optional(dict)
    
# --------------------------------------------------------------------

@injected
class DefinitionHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the definitions info merge with the solicitation and invoker info.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker, Solicitation=Solicitation, Definition=Definition)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the register definitions.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        
        if not register.invokers: return  # No invokers to process
        
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            if not invoker.definitions: continue  # No definitions, move along.
            
            for defin in invoker.definitions:
                assert isinstance(defin, Definition), 'Invalid definition %s' % defin
        
                if defin.info is None: defin.info = {}
                if Definition.solicitation in defin and defin.solicitation:
                    sol = defin.solicitation
                    assert isinstance(sol, Solicitation), 'Invalid solicitation %s' % sol
                    
                    while sol:
                        if Solicitation.info in sol and sol.info:
                            for key, value in sol.info.items():
                                if key not in defin.info: defin.info[key] = value
                        if Solicitation.invoker in sol and sol.invoker:
                            if Invoker.info in sol.invoker:
                                assert isinstance(sol.invoker, Invoker), 'Invalid invoker %s' % sol.invoker
                                if sol.invoker.info:
                                    for key, value in sol.invoker.info.items():
                                        if key not in defin.info: defin.info[key] = value
                                
                        if Solicitation.solicitation in sol: sol = sol.solicitation
                        else: sol = None
