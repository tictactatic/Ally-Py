'''
Created on Jul 24, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexing for content decoding.
'''

from ..general import index
from ..general.index import IndexDecode
from ally.api.type import Type
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.support.util import firstOf
from ally.support.util_context import listing, iterate

# --------------------------------------------------------------------

class Decoding(index.Decoding):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    contentDefinitions = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The definition context for the content decoding indexed by category.
    ''')
    # ---------------------------------------------------------------- Required
    name = requires(str)
    children = requires(dict)
    
class Definition(index.DefinitionDecoding):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The definition name.
    ''')

# --------------------------------------------------------------------

@injected
class IndexContentDecode(IndexDecode):
    '''
    Implementation for a handler that provides the indexing for content decoding.
    '''
    
    separator = None
    # The separator to use for content names, if not provided the names will be placed as simple names.
    
    def __init__(self):
        assert self.separator is None or isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__(decoding=Decoding, Definition=Definition)
        
    def processDefinition(self, decoding, **keyargs):
        '''
        @see: IndexDecode.processDefinition
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if decoding.contentDefinitions is None: decoding.contentDefinitions = {}
        
        keyargs.update(decoding=decoding, definition=decoding.contentDefinitions.get(self.category))
        definition = decoding.contentDefinitions[self.category] = super().processDefinition(**keyargs)
        assert isinstance(definition, Definition), 'Invalid definition %s' % definition
        if self.separator: definition.name = self.separator.join(reversed(listing(decoding, Decoding.parent, Decoding.name)))
        else: definition.name = decoding.name
        
        if not definition.types:
            for primitive in iterate(decoding, lambda decoding: firstOf(decoding.children.values())
                                     if len(decoding.children) == 1 else None):
                assert isinstance(primitive, Decoding), 'Invalid decoding %s' % primitive
                assert isinstance(primitive.type, Type), 'Invalid decoding type %s' % primitive.type
                
                if primitive.type.isPrimitive:
                    if definition.types is None: definition.types = []
                    definition.types.append(primitive.type)
                    break

        return definition
        
