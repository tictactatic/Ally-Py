'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the primitive properties encoder.
'''

from ally.api.operator.type import TypeProperty
from ally.api.type import Iter, Type, Dict
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer, Converter
from ally.core.spec.transform.encoder import IEncoder
from ally.core.spec.transform.render import IRender
from ally.core.spec.transform.representation import Property, Object
from ally.design.cache import CacheWeak
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from collections import Iterable

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder for the property.
    ''')    
    # ---------------------------------------------------------------- Required
    name = requires(str)
    objType = requires(object)

class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Optional
    converter = optional(Converter)
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
    
# --------------------------------------------------------------------

@injected
class PropertyEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the primitive properties values encoding.
    '''
    
    def __init__(self):
        super().__init__(support=Support)
        
        self._cache = CacheWeak()
        
    def process(self, create:Create, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Create the property encoder.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypeProperty): return 
        # The type is not for a property, nothing to do, just move along
        
        valueType = create.objType.type
        assert isinstance(create.name, str), 'Invalid property name %s' % create.name
        
        cache = self._cache.key(create.name, valueType)
        if not cache.has: cache.value = EncoderProperty(create.name, valueType)
            
        create.encoder = cache.value

# --------------------------------------------------------------------

class EncoderProperty(IEncoder):
    '''
    Implementation for a @see: IEncoder for properties.
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
        assert Support.converter in support, 'No converter available in %s' % support
        assert isinstance(support.converter, Converter), 'Invalid converter %s' % support.converter
        
        if isinstance(self.valueType, Iter):
            assert isinstance(obj, Iterable), 'Invalid object %s' % obj
            itemType = self.valueType.itemType
            obj = [support.converter.asString(item, itemType) for item in obj]
            render.property(support.normalizer.normalize(self.name), obj)
        elif isinstance(self.valueType, Dict):
            assert isinstance(obj, dict), 'Invalid object %s' % obj
            keyType = self.valueType.keyType
            valueType = self.valueType.valueType
            obj = {support.converter.asString(key, keyType): support.converter.asString(item, valueType)
                   for key, item in obj.items()}
            render.property(support.normalizer.normalize(self.name), obj)
        else:
            render.property(support.normalizer.normalize(self.name), support.converter.asString(obj, self.valueType))
        
    def represent(self, support, obj=None):
        '''
        @see: IEncoder.represent
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer

        property = Property(support.normalizer.normalize(self.name))
        
        if obj:
            assert isinstance(obj, Object), 'Invalid representation object to push in %s' % obj
            obj.properties.append(property)
            
        else: return property
