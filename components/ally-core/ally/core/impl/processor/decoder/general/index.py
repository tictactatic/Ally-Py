'''
Created on Jul 24, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexing for decoding.
'''

from ally.api.type import Type, Input
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_context import findFirst
from ally.support.util_spec import IDo

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    solved = defines(set, doc='''
    @rtype: set(object)
    The input of the caller that are solved on the invoker.
    ''')
    definitions = defines(list, doc='''
    @rtype: list[Context]
    Definitions containing representative data for invoker decoders.
    ''')
    
class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Optional
    parent = optional(Context)
    # ---------------------------------------------------------------- Required
    input = requires(Input)
    type = requires(Type)
    doDecode = requires(IDo)
    
class DefinitionDecoding(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    decoding = defines(Context, doc='''
    @rtype: Context
    The decoding that the definition belongs to.
    ''')
    category = defines(str, doc='''
    @rtype: string
    The decoding category name.
    ''')
    types = defines(list, doc='''
    @rtype: list[Type]
    The definition types in the normal order of the appearance.
    ''')

# --------------------------------------------------------------------

@injected
class IndexDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the indexing for decoding.
    '''
    
    category = str
    # The definition category to set.
    
    def __init__(self, decoding=Decoding, invoker=Invoker, Definition=DefinitionDecoding, **contexts):
        assert isinstance(self.category, str), 'Invalid definition category %s' % self.category
        super().__init__(decoding=decoding, invoker=invoker, Definition=Definition, **contexts)
        
    def process(self, chain, decoding:Context, invoker:Context, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the definition for decoding.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        
        if not decoding.doDecode: return
        assert isinstance(decoding.type, Type), 'Invalid decoding type %s' % decoding.type
        
        
        inp = findFirst(decoding, Decoding.parent, Decoding.input)
        if inp:
            if invoker.solved is None: invoker.solved = set()
            invoker.solved.add(inp)
     
        self.processDefinition(decoding=decoding, invoker=invoker, **keyargs)

    # ----------------------------------------------------------------
    
    def processDefinition(self, decoding, invoker, Definition, definition=None, **keyargs):
        '''
        Process the definition for indexing.
        
        @return: Context|None
            The definition context if one was indexed, otherwise provides None.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(decoding.type, Type), 'Invalid decoding type %s' % decoding.type
        
        if not definition: definition = Definition()
        assert isinstance(definition, DefinitionDecoding), 'Invalid definition %s' % definition
        
        definition.decoding = decoding
        definition.category = self.category
        
        if decoding.type.isPrimitive and not definition.types:
            if definition.types is None: definition.types = []
            definition.types.append(decoding.type)
            
        if invoker.definitions is None: invoker.definitions = []
        invoker.definitions.append(definition)
        
        return definition
