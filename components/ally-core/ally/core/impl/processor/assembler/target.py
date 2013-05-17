'''
Created on May 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoker target model.
'''

from ally.api.config import GET, DELETE, INSERT, UPDATE
from ally.api.operator.type import TypeModel, TypeModelProperty
from ally.api.type import Iter, Input
from ally.core.spec.resources import Invoker
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    report = defines(list, doc='''
    @rtype: list[string]
    The report on the assembly.
    ''')
    # ---------------------------------------------------------------- Required
    callers = requires(list)
    
class Caller(Context):
    '''
    The register caller context.
    '''
    # ---------------------------------------------------------------- Defined
    model = defines(TypeModel, doc='''
    @rtype: TypeModel
    The model type that is the target of the invoker.
    ''')
    isCollection = defines(bool, doc='''
    @rtype: boolean
    Flag indicating that the invoker reflects a collection of model.
    ''')
    # ---------------------------------------------------------------- Required
    invoker = requires(Invoker)
    location = requires(str)

# --------------------------------------------------------------------

class TargetModelHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the target model of the invoker.
    '''
    
    def __init__(self):
        super().__init__(Caller=Caller)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the target model.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(register.callers, list), 'Invalid callers %s' % register.callers

        callers = []
        for caller in register.callers:
            assert isinstance(caller, Caller), 'Invalid caller %s' % caller
            assert isinstance(caller.invoker, Invoker), 'Invalid invoker %s' % caller.invoker
            
            caller.isCollection, model = False, None
            
            if caller.invoker.method == GET:
                if isinstance(caller.invoker.output, Iter):
                    assert isinstance(caller.invoker.output, Iter)
                    model = caller.invoker.output.itemType
                    caller.isCollection = True
                else: model = caller.invoker.output
        
                if isinstance(model, TypeModelProperty):
                    assert isinstance(model, TypeModelProperty)
                    model = model.parent
            elif caller.invoker.method == DELETE:
                for inp in caller.invoker.inputs[:caller.invoker.mandatory]:
                    assert isinstance(inp, Input), 'Invalid input %s' % inp
                    if isinstance(inp.type, TypeModelProperty):
                        assert isinstance(inp.type, TypeModelProperty)
                        model = inp.type.parent
                        break
            elif caller.invoker.method == INSERT:
                if isinstance(caller.invoker.output, (TypeModel, TypeModelProperty)):
                    model = caller.invoker.output.container
            elif caller.invoker.method == UPDATE:
                for inp in caller.invoker.inputs[:caller.invoker.mandatory]:
                    assert isinstance(inp, Input), 'Invalid input %s' % inp
                    if isinstance(inp.type, TypeModel):
                        model = inp.type
                        break
                
            if not isinstance(model, TypeModel):
                if register.report is None: register.report = []
                register.report.append('Cannot extract the target model for:')
                register.report.append(caller.location)
            else:
                caller.model = model
                callers.append(caller)
                    
