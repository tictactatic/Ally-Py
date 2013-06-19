'''
Created on Jun 19, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the definitions tree build.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from collections import deque

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
    # ---------------------------------------------------------------- Required
    definitions = requires(dict)

class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    definitions = defines(set, doc='''
    @rtype: set(Context)
    The child definitions.
    ''')
    # ---------------------------------------------------------------- Required
    parent = requires(Context)
    isOptional = requires(bool)

# --------------------------------------------------------------------

@injected
class DecodingDefinitionsHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the definitions arrangements.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker, Definition=Definition)
        
    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the definitions arrangements.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return  # No invokers to process.
        
        definitions = deque()
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if not invoker.definitions: continue
            
            topDefinitions = []
            definitions.extend(invoker.definitions.values())
            while definitions:
                definition = definitions.popleft()
                assert isinstance(definition, Definition), 'Invalid definition %s' % definition
                
                if definition.parent:
                    assert isinstance(definition.parent, Definition), 'Invalid definition %s' % definition.parent
                    if definition.parent.definitions is None: definition.parent.definitions = set()
                    definition.parent.definitions.add(definition)
                    definitions.append(definition.parent)
                else: topDefinitions.append(definition)
            
            for top in topDefinitions:
                assert isinstance(top, Definition), 'Invalid definition %s' % top
                if top.isOptional is None: continue  # No clear value to propagate.
                if not top.definitions: continue
                
                definitions.extend(top.definitions)
                while definitions:
                    definition = definitions.popleft()
                    definition.isOptional = top.isOptional
                    if definition.definitions: definitions.extend(definition.definitions)
