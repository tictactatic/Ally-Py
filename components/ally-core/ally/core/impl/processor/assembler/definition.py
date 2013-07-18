'''
Created on Jul 13, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides general register definitions.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_context import namesOf, pushIn

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    definitions = defines(list, doc='''
    @rtype: list[Context]
    Definitions containing representative data for register, more or lease a global definition scope.
    ''')

class DefinitionPopulate(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    category = defines(str, doc='''
    @rtype: string
    The category of the definition.
    ''')
    name = defines(str, doc='''
    @rtype: string
    The name of the definition.
    ''')
    type = defines(Type, doc='''
    @rtype: Type
    The type of the definition.
    ''')
    enumeration = defines(list, doc='''
    @rtype: list[string]
    The enumeration values that are allowed for order.
    ''')
    
# --------------------------------------------------------------------

@injected
class DefinitionHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides general definitions.
    '''
    
    definitions = list
    # The list of definitions dictionaries to inject in register.
    
    def __init__(self):
        assert isinstance(self.definitions, list), 'Invalid definitions %s' % self.definitions
        if __debug__:
            keys = namesOf(DefinitionPopulate)
            for data in self.definitions:
                assert isinstance(data, dict), 'Invalid definition data %s' % data
                assert keys.issuperset(data), 'The available data keys are %s, invalid %s' % (', '.join(keys), data) 
        super().__init__()

    def process(self, chain, register:Register, Definition:DefinitionPopulate, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the register definitions.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Definition, DefinitionPopulate), 'Invalid definition class %s' % Definition
        
        if register.definitions is None: register.definitions = []
        for data in self.definitions: register.definitions.append(pushIn(Definition(), data))
        
