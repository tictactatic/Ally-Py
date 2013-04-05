'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the id properties encoder.
'''

from ally.api.operator.type import TypeModelProperty
from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer, Converter
from ally.core.spec.transform.encoder import IEncoder
from ally.core.spec.transform.render import IRender
from ally.design.cache import CacheWeak
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder for the id property.
    ''')   
    # ---------------------------------------------------------------- Required
    name = requires(str)
    objType = requires(object)

class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Optional
    converterId = optional(Converter)
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
    
# --------------------------------------------------------------------

@injected
class PropertyIdEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the id properties values encoding.
    '''
    
    def __init__(self):
        super().__init__(support=Support)
        
        self._cache = CacheWeak()
        
    def process(self, create:Create, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Create the id property encoder.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypeModelProperty): return
        # The type is not for a property, nothing to do, just move along
        assert isinstance(create.objType, TypeModelProperty)
        if not create.objType.isId():  return
        # Not a id property, nothing to do, just move along
        
        assert isinstance(create.name, str), 'Invalid property name %s' % create.name
        
        cache = self._cache.key(create.name, create.objType.type)
        if not cache.has: cache.value = EncoderPropertyId(create.name, create.objType.type)
            
        create.encoder = cache.value

# --------------------------------------------------------------------

class EncoderPropertyId(IEncoder):
    '''
    Implementation for a @see: IEncoder for id properties.
    '''
    
    def __init__(self, name, valueType):
        '''
        Construct the property encoder.
        '''
        assert isinstance(name, str), 'Invalid property name %s' % name
        assert isinstance(valueType, Type), 'Invalid value type %s' % valueType
        self.name = name
        self.valueType = valueType
        
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert Support.converterId in support, 'No id converter available in %s' % support
        assert isinstance(support.converterId, Converter), 'Invalid id converter %s' % support.converterId
        
        render.property(support.normalizer.normalize(self.name), support.converterId.asString(obj, self.valueType))
