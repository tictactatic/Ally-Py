'''
Created on Jun 14, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the option decoding.
'''

from ally.api.operator.type import TypeProperty, TypeOption
from ally.api.type import Type
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
    property = defines(TypeProperty, doc='''
    @rtype: TypeProperty
    The option property.
    ''')
    # ---------------------------------------------------------------- Required
    type = requires(Type)    
    
# --------------------------------------------------------------------

@injected
class OptionDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the primitive properties values encoding.
    '''
    
    def process(self, chain, decoding:Decoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the option type decoding.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if isinstance(decoding.type, TypeProperty) and isinstance(decoding.type.parent, TypeOption):
            assert isinstance(decoding.type, TypeProperty)
            decoding.property = decoding.type
            decoding.type = decoding.type.type
