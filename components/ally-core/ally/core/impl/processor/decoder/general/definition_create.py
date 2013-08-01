'''
Created on Jul 26, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the definition creation.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_spec import IDo

# --------------------------------------------------------------------
 
class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Optional
    isMandatory = optional(bool)
    # ---------------------------------------------------------------- Required
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
    isMandatory = defines(bool, doc='''
    @rtype: boolean
    Indicates that the definition requires a value.
    ''')

# --------------------------------------------------------------------

@injected
class DefinitionCreateHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the definition creation.
    '''
    
    category = str
    # The definition category to set.
    
    def __init__(self):
        assert isinstance(self.category, str), 'Invalid definition category %s' % self.category
        super().__init__()
        
    def process(self, chain, decoding:Decoding, Definition:DefinitionDecoding, definition:Context=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the definition for decoding.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if not decoding.doDecode: return
        
        if definition:
            assert isinstance(definition, DefinitionDecoding), 'Invalid definition %s' % definition
            if definition.category is not None and definition.category != self.category: definition = None
        
        if not definition:
            definition = Definition()
            chain.process(definition=definition)
        
        definition.decoding = decoding
        definition.category = self.category
        if Decoding.isMandatory in decoding: definition.isMandatory = decoding.isMandatory
        
        if decoding.type and decoding.type.isPrimitive and not definition.types:
            assert isinstance(decoding.type, Type), 'Invalid type %s' % decoding.type
            if definition.types is None: definition.types = []
            definition.types.append(decoding.type)
            
