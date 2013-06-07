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
from ally.core.spec.transform.encoder import IEncoder, EncoderWithSpecifiers
from ally.core.spec.transform.index import NAME_BLOCK
from ally.core.spec.transform.render import IRender
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional, \
    definesIf
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.exception import DevelError

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    hideProperties = requires(bool)

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
class ModelEncode(HandlerBranching):
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
        super().__init__(Branch(self.propertyEncodeAssembly).included().using(create=CreateProperty),
                         Branch(self.modelExtraEncodeAssembly).included().using(create=CreateModelExtra))
        
        self.typeOrders = [typeFor(typ) for typ in self.typeOrders]
        
    def process(self, chain, propertyProcessing, modelExtraProcessing, invoker:Invoker, create:Create, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the model encoder.
        '''
        assert isinstance(propertyProcessing, Processing), 'Invalid processing %s' % propertyProcessing
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
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
        
        properties, extra = [], None
        if not invoker.hideProperties:
            for propType in self.sortedTypes(create.objType):
                assert isinstance(propType, TypeProperty), 'Invalid property type %s' % propType
                arg = propertyProcessing.execute(create=propertyProcessing.ctx.create(objType=propType, name=propType.property),
                                                 invoker=invoker, **keyargs)
                assert isinstance(arg.create, CreateProperty), 'Invalid create property %s' % arg.create
                if arg.create.encoder is None: raise DevelError('Cannot encode %s' % propType)
                properties.append((propType.property, arg.create.encoder))
        
            if modelExtraProcessing:
                assert isinstance(modelExtraProcessing, Processing), 'Invalid processing %s' % modelExtraProcessing
                arg = modelExtraProcessing.execute(create=modelExtraProcessing.ctx.create(objType=create.objType),
                                                   invoker=invoker, **keyargs)
                assert isinstance(arg.create, CreateModelExtra), 'Invalid create model extra %s' % arg.create
                if CreateModelExtra.encoder in arg.create: extra = arg.create.encoder
            
        create.encoder = EncoderModel(name, properties, extra, specifiers)

    # --------------------------------------------------------------------
    
    def sortedTypes(self, model):
        '''
        Provides the sorted properties type for the model type.
        '''
        assert isinstance(model, TypeModel), 'Invalid type model %s' % model
        sorted = list(model.propertyTypes())
        if model.hasId(): sorted.remove(model.propertyTypeId())
        sorted.sort(key=lambda propType: propType.property)
        sorted.sort(key=self.sortKey)
        if model.hasId(): sorted.insert(0, model.propertyTypeId())
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
        
        if not self.properties:
            render.beginObject(self.name, **self.populate(obj, support, indexBlock=NAME_BLOCK))
        else:
            render.beginObject(self.name, **self.populate(obj, support))
            for name, encoder in self.properties:
                assert isinstance(encoder, IEncoder), 'Invalid property encoder %s' % encoder
                objValue = getattr(obj, name)
                if objValue is None: continue
                encoder.render(objValue, render, support)
                
            if self.extra: self.extra.render(obj, render, support)
                
        render.end()
