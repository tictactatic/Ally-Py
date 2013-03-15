'''
Created on Mar 7, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the model encoder.
'''

from ally.api.operator.container import Model
from ally.api.operator.type import TypeModel, TypeProperty, TypeModelProperty
from ally.api.type import Iter, Boolean, Integer, Number, Percentage, String, \
    Time, Date, DateTime, typeFor
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer
from ally.core.spec.transform.encoder import IAttributes, IEncoder
from ally.core.spec.transform.render import IRender
from ally.design.cache import CacheWeak
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.branch import Included
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranchingProceed
from ally.exception import DevelError

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder for the model.
    ''')
    # ---------------------------------------------------------------- Optional
    name = optional(str)
    attributes = optional(IAttributes)
    # ---------------------------------------------------------------- Required
    objType = requires(object)
    
class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
    
class CreateProperty(Context):
    '''
    The create property encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The name used to render the property with.
    ''')
    objType = defines(object, doc='''
    @rtype: object
    The property type.
    ''')
    # ---------------------------------------------------------------- Required
    encoder = requires(IEncoder)
    
# --------------------------------------------------------------------

@injected
class ModelEncode(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the model encoding.
    '''
    
    propertyEncodeAssembly = Assembly
    # The encode processors to be used for encoding properties.
    typeOrders = [Boolean, Integer, Number, Percentage, String, Time, Date, DateTime, Iter]
    # The type that define the order in which the properties should be rendered.
    
    def __init__(self):
        assert isinstance(self.propertyEncodeAssembly, Assembly), \
        'Invalid property encode assembly %s' % self.propertyEncodeAssembly
        assert isinstance(self.typeOrders, list), 'Invalid type orders %s' % self.typeOrders
        super().__init__(Included(self.propertyEncodeAssembly, create=CreateProperty), support=Support)
        
        self.typeOrders = [typeFor(typ) for typ in self.typeOrders]
        self._cache = CacheWeak()
        
    def process(self, propertyProcessing, create:Create, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Create the model encoder.
        '''
        assert isinstance(propertyProcessing, Processing), 'Invalid processing %s' % propertyProcessing
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if isinstance(create.objType, TypeModel):
            modelType = create.objType
            propType = None
        elif isinstance(create.objType, TypeModelProperty):
            modelType = create.objType.parent
            propType = create.objType
        else: return
        # The type is not for a model, nothing to do, just move along
        
        assert isinstance(modelType, TypeModel)
        assert isinstance(modelType.container, Model)
        
        if Create.name in create and create.name: name = create.name
        else: name = modelType.container.name
        if Create.attributes in create: attributes = create.attributes
        else: attributes = None
        
        if propType:
            cache = self._cache.key(propertyProcessing, name, attributes, propType)
            if not cache.has:
                encoderProperty = self.propertyEncoder(propType, propertyProcessing, keyargs)
                cache.value = EncoderModelProperty(name, encoderProperty, attributes)
                
        else:
            cache = self._cache.key(propertyProcessing, name, attributes, modelType)
            if not cache.has:
                properties = []
                for propType in self.sortedTypes(create.objType):
                    encoderProperty = self.propertyEncoder(propType, propertyProcessing, keyargs)
                    properties.append((propType.property, encoderProperty))
                cache.value = EncoderModel(name, properties, attributes)
        
        create.encoder = cache.value
        
    # --------------------------------------------------------------------
    
    def propertyEncoder(self, propertyType, processing, keyargs):
        '''
        Provides the property encoder.
        '''
        assert isinstance(propertyType, TypeProperty), 'Invalid property type %s' % propertyType
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        chain = Chain(processing)
        chain.process(create=processing.ctx.create(objType=propertyType, name=propertyType.property), **keyargs).doAll()
        create = chain.arg.create
        assert isinstance(create, CreateProperty), 'Invalid create property %s' % create
        if create.encoder is None: raise DevelError('Cannot encode %s' % propertyType)
        return create.encoder
    
    def sortedTypes(self, modelType):
        '''
        Provides the sorted properties type for the model type.
        '''
        assert isinstance(modelType, TypeModel), 'Invalid type model %s' % modelType
        sorted = list(modelType.propertyTypes())
        if modelType.hasId(): sorted.remove(modelType.propertyTypeId())
        sorted.sort(key=lambda propType: propType.property)
        sorted.sort(key=self.sortKey)
        if modelType.hasId(): sorted.insert(0, modelType.propertyTypeId())
        return sorted
    
    def sortKey(self, propType):
        '''
        Provides the sorting key for property types, used in sort functions.
        '''
        assert isinstance(propType, TypeProperty), 'Invalid property type %s' % propType

        for k, ord in enumerate(self.typeOrders):
            if propType.type == ord: break
        return k

# --------------------------------------------------------------------

class EncoderModel(IEncoder):
    '''
    Implementation for a @see: IEncoder for model.
    '''
    
    def __init__(self, name, properties, attributes=None):
        '''
        Construct the model encoder.
        '''
        assert isinstance(name, str), 'Invalid model name %s' % name
        assert isinstance(properties, list), 'Invalid properties %s' % properties
        assert attributes is None or isinstance(attributes, IAttributes), 'Invalid attributes %s' % attributes
        
        self.name = name
        self.properties = properties
        self.attributes = attributes
        
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        
        if self.attributes: attributes = self.attributes.provide(obj, support)
        else: attributes = None
        render.objectStart(support.normalizer.normalize(self.name), attributes)
        
        for name, encoder in self.properties:
            assert isinstance(encoder, IEncoder), 'Invalid property encoder %s' % encoder
            objValue = getattr(obj, name)
            if objValue is None: continue
            encoder.render(objValue, render, support)
        
        render.objectEnd()

class EncoderModelProperty(IEncoder):
    '''
    Implementation for a @see: IEncoder for model property.
    '''
    
    def __init__(self, name, encoder, attributes=None):
        '''
        Construct the model property encoder.
        '''
        assert isinstance(name, str), 'Invalid model name %s' % name
        assert isinstance(encoder, IEncoder), 'Invalid property encoder %s' % encoder
        assert attributes is None or isinstance(attributes, IAttributes), 'Invalid attributes %s' % attributes
        
        self.name = name
        self.encoder = encoder
        self.attributes = attributes
        
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        
        if self.attributes: attributes = self.attributes.provide(obj, support)
        else: attributes = None
        render.objectStart(support.normalizer.normalize(self.name), attributes)
        self.encoder.render(obj, render, support)
        render.objectEnd()

