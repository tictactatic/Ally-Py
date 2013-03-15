'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the primitive properties encoder.
'''

from ally.api.operator.type import TypeProperty
from ally.api.type import Iter, Type
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer, Converter
from ally.core.spec.transform.encoder import IEncoder
from ally.core.spec.transform.render import IRender
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from collections import Iterable
from ally.design.cache import CacheWeak

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
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
    converter = requires(Converter)
    
# --------------------------------------------------------------------

@injected
class PropertyEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the primitive properties values encoding.
    '''
    
    nameValue = 'Value'
    # The name to use for rendering the values in a collection property.
    
    def __init__(self):
        assert isinstance(self.nameValue, str), 'Invalid name value list %s' % self.nameValue
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
        if not cache.has:
            if isinstance(valueType, Iter):
                assert isinstance(valueType, Iter)
                cache.value = EncoderPropertyCollection(create.name, self.nameValue, valueType.itemType)
                
            else:
                cache.value = EncoderProperty(create.name, valueType)
            
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
        assert isinstance(support.converter, Converter), 'Invalid converter %s' % support.converter
        
        render.value(support.normalizer.normalize(self.name), support.converter.asString(obj, self.valueType))
        
class EncoderPropertyCollection(IEncoder):
    '''
    Implementation for a @see: IEncoder for properties that contains a collection.
    '''
    
    def __init__(self, name, nameValue, valueType):
        '''
        Construct the property encoder.
        '''
        assert isinstance(name, str), 'Invalid property name %s' % name
        assert isinstance(nameValue, str), 'Invalid value name %s' % nameValue
        assert isinstance(valueType, Type), 'Invalid value type %s' % valueType
        self.name = name
        self.nameValue = nameValue
        self.valueType = valueType
        
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(obj, Iterable), 'Invalid encode object %s' % obj
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert isinstance(support.converter, Converter), 'Invalid converter %s' % support.converter
        
        render.collectionStart(support.normalizer.normalize(self.name))
        nameValue = support.normalizer.normalize(self.nameValue)
        for objItem in obj: render.value(nameValue, support.converter.asString(objItem, self.valueType))
        render.collectionEnd()
