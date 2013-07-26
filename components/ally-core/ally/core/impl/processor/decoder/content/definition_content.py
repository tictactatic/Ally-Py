'''
Created on Jul 24, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexing for content definitions.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.support.util import firstOf
from ally.support.util_context import listing, iterate
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    contentDefinitions = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The definition context for the content decoding indexed by category.
    ''')
    # ---------------------------------------------------------------- Required
    parent = requires(Context)
    name = requires(str)
    children = requires(dict)
    
class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The definition name.
    ''')
    types = defines(list, doc='''
    @rtype: list[Type]
    The definition types in the normal order of the appearance.
    ''')
    references = defines(list, doc='''
    @rtype: list[Context]
    The definition references that directly linked with this definition.
    ''')
    # ---------------------------------------------------------------- Required
    category = requires(str)

# --------------------------------------------------------------------

@injected
class DefinitionContentHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the indexing for content definitions.
    '''
    
    separator = None
    # The separator to use for content names, if not provided the names will be placed as simple names.
    
    def __init__(self):
        assert self.separator is None or isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__(Definition=Definition)
        
    def process(self, chain, decoding:Decoding, definition:Context=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Index the definition for content.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if not definition: return
        assert isinstance(definition, Definition), 'Invalid definition %s' % definition
        
        if decoding.contentDefinitions is None: decoding.contentDefinitions = {}
        assert isinstance(definition.category, str), 'Invalid definition category %s' % definition.category
        assert definition.category not in decoding.contentDefinitions, 'Already a definition for \'%s\'' % definition.category
        
        decoding.contentDefinitions[definition.category] = definition
        if self.separator: definition.name = self.separator.join(reversed(listing(decoding, Decoding.parent, Decoding.name)))
        else: definition.name = decoding.name
        
        if decoding.children:
            for child in decoding.children.values():
                assert isinstance(child, Decoding), 'Invalid decoding %s' % child
                if child.contentDefinitions and definition.category in child.contentDefinitions:
                    if definition.references is None: definition.references = []
                    definition.references.append(child.contentDefinitions[definition.category])
        
        if not definition.types:
            for child in iterate(decoding, lambda decoding: firstOf(decoding.children.values())
                                 if decoding.children and len(decoding.children) == 1 else None):
                assert isinstance(child, Decoding), 'Invalid decoding %s' % child
                
                if child.type and child.type.isPrimitive:
                    assert isinstance(child.type, Type), 'Invalid decoding type %s' % child.type
                    if definition.types is None: definition.types = []
                    definition.types.append(child.type)
                    break

        return definition
        
