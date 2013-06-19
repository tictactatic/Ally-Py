'''
Created on Jun 14, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the option parameters decoding.
'''

from ally.api.operator.type import TypeProperty, TypeOption
from ally.api.type import Type
from ally.container.ioc import injected
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create decoder context.
    '''
    # ---------------------------------------------------------------- Defined
    solicitaions = requires(list)
                   
class Solicitaion(Context):
    '''
    The decoder solicitaion context.
    '''
    # ---------------------------------------------------------------- Defined
    objType = defines(Type, doc='''
    @rtype: Type
    The option type if is the case.
    ''')    
    
# --------------------------------------------------------------------

@injected
class OptionParameterDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the primitive properties values encoding.
    '''
    
    def __init__(self):
        super().__init__(Solicitaion=Solicitaion)
    
    def process(self, chain, create:Create, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the property encoder.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if not create.solicitaions: return 
        # There is not solicitaion to process.
        
        for sol in create.solicitaions:
            assert isinstance(sol, Solicitaion), 'Invalid solicitation %s' % sol
        
            if isinstance(sol.objType, TypeProperty) and isinstance(sol.objType.parent, TypeOption):
                assert isinstance(sol.objType, TypeProperty)
                sol.objType = sol.objType.type  # Is an option type.
