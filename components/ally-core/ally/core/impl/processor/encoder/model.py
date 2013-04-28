'''
Created on Mar 7, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the model encoder.
'''

from ally.api.operator.container import Model
from ally.api.operator.type import TypeModel, TypeProperty
from ally.api.type import Iter, Boolean, Integer, Number, Percentage, String, \
    Time, Date, DateTime, typeFor
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer
from ally.core.spec.transform.encoder import IEncoder, EncoderWithSpecifiers
from ally.core.spec.transform.render import IRender
from ally.design.cache import CacheWeak
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional, \
    definesIf
from ally.design.processor.branch import Included
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranchingProceed
from ally.exception import DevelError
from ally.core.spec.transform.index import NAME_BLOCK

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
    specifiers = optional(list)
    # ---------------------------------------------------------------- Required
    objType = requires(object)
    
class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Optional
    hideProperties = optional(bool)
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
    
class CreateModelExtra(Context):
    '''
    The create extra model encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    objType = definesIf(object, doc='''
    @rtype: object
    The model type.
    ''')
    # ---------------------------------------------------------------- Optional
    encoder = optional(IEncoder)
    
# --------------------------------------------------------------------

@injected
class ModelEncode(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the model encoding.
    '''
    
    propertyEncodeAssembly = Assembly
    # The encode processors to be used for encoding properties.
    modelExtraEncodeAssembly = Assembly
    # The encode processors to be used for encoding extra data on the model.
    typeOrders = [Boolean, Integer, Number, Percentage, String, Time, Date, DateTime, Iter]
    # The type that define the order in which the properties should be rendered.
    
    def __init__(self):
        assert isinstance(self.propertyEncodeAssembly, Assembly), \
        'Invalid property encode assembly %s' % self.propertyEncodeAssembly
        assert isinstance(self.modelExtraEncodeAssembly, Assembly), \
        'Invalid model extra encode assembly %s' % self.modelExtraEncodeAssembly
        assert isinstance(self.typeOrders, list), 'Invalid type orders %s' % self.typeOrders
        super().__init__(Included(self.propertyEncodeAssembly).using(create=CreateProperty),
                         Included(self.modelExtraEncodeAssembly).using(create=CreateModelExtra), support=Support)
        
        self.typeOrders = [typeFor(typ) for typ in self.typeOrders]
        self._cache = CacheWeak()
        
    def process(self, propertyProcessing, modelExtraProcessing, create:Create, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Create the model encoder.
        '''
        assert isinstance(propertyProcessing, Processing), 'Invalid processing %s' % propertyProcessing
        assert isinstance(modelExtraProcessing, Processing), 'Invalid processing %s' % modelExtraProcessing
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypeModel): return
        # The type is not for a model, nothing to do, just move along
        assert isinstance(create.objType, TypeModel)
        assert isinstance(create.objType.container, Model)
        
        if Create.name in create and create.name: name = create.name
        else: name = create.objType.container.name
        if Create.specifiers in create: specifiers = create.specifiers or ()
        else: specifiers = ()
        
        cache = self._cache.key(propertyProcessing, modelExtraProcessing, name, create.objType, *specifiers)
        if not cache.has:
            properties = []
            for propType in self.sortedTypes(create.objType):
                assert isinstance(propType, TypeProperty), 'Invalid property type %s' % propType
                chain = Chain(propertyProcessing)
                chain.process(create=propertyProcessing.ctx.create(objType=propType, name=propType.property), **keyargs).doAll()
                propCreate = chain.arg.create
                assert isinstance(propCreate, CreateProperty), 'Invalid create property %s' % propCreate
                if propCreate.encoder is None: raise DevelError('Cannot encode %s' % propType)
                properties.append((propType.property, propCreate.encoder))
            
            chain = Chain(modelExtraProcessing)
            chain.process(create=modelExtraProcessing.ctx.create(objType=create.objType), **keyargs).doAll()
            extraCreate = chain.arg.create
            assert isinstance(extraCreate, CreateModelExtra), 'Invalid create model extra %s' % extraCreate
            if CreateModelExtra.encoder in extraCreate: extra = extraCreate.encoder
            else: extra = None
                
            cache.value = EncoderModel(name, properties, extra, specifiers)
        
        create.encoder = cache.value
        
    # --------------------------------------------------------------------
    
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

class EncoderModel(EncoderWithSpecifiers):
    '''
    Implementation for a @see: IEncoder for model.
    '''
    
    def __init__(self, name, properties, extra=None, specifiers=None):
        '''
        Construct the model encoder.
        '''
        assert isinstance(name, str), 'Invalid model name %s' % name
        assert isinstance(properties, list), 'Invalid properties %s' % properties
        assert extra is None or isinstance(extra, IEncoder), 'Invalid extra encoder %s' % extra
        super().__init__(specifiers)
        
        self.name = name
        self.properties = properties
        self.extra = extra
        
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        
        if Support.hideProperties in support and support.hideProperties is not None:
            hideProperties = support.hideProperties
        else: hideProperties = False
        
        if hideProperties:
            render.beginObject(support.normalizer.normalize(self.name),
                           **self.populate(obj, support, indexBlock=NAME_BLOCK))
        else:
            render.beginObject(support.normalizer.normalize(self.name), **self.populate(obj, support))
            for name, encoder in self.properties:
                assert isinstance(encoder, IEncoder), 'Invalid property encoder %s' % encoder
                objValue = getattr(obj, name)
                if objValue is None: continue
                encoder.render(objValue, render, support)
                
            if self.extra: self.extra.render(obj, render, support)
                
        render.end()
