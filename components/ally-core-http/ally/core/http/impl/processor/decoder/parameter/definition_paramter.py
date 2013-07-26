'''
Created on Jul 24, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexing for parameter decoding.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    parameterDefinition = defines(Context, doc='''
    @rtype: Context
    The definition context for the parameter decoding.
    ''')
      
class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The definition name.
    ''')
    
class Parameter(Context):
    '''
    The parameter context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(list)

# --------------------------------------------------------------------

@injected
class DefinitionParameterHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the indexing for parameter decoding.
    '''
    
    separator = '.'
    # The separator to use for parameter names.
    
    def __init__(self):
        assert isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__(Definition=Definition)
        
    def process(self, chain, decoding:Decoding, parameter:Parameter, definition:Context=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Index the definition for parameter.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(parameter, Parameter), 'Invalid parameter %s' % parameter
        
        if not definition: return
        assert isinstance(definition, Definition), 'Invalid definition %s' % definition
        assert decoding.parameterDefinition is None, 'Decoding %s already has a definition' % decoding.parameterDefinition
        
        definition.name = self.separator.join(parameter.path)
        decoding.parameterDefinition = definition
