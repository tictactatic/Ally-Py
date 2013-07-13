'''
Created on Mar 7, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the model encoder.
'''

from ally.api.operator.type import TypeModel, TypeProperty
from ally.api.type import Iter, Boolean, Integer, Number, String, Time, Date, \
    DateTime, typeFor
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IEncoder, EncoderWithSpecifiers, \
    IRender
from ally.core.spec.transform.index import NAME_BLOCK
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional, \
    definesIf
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranching
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

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
    isCorrupted = definesIf(bool)
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
    typeOrders = [Boolean, Integer, Number, String, Time, Date, DateTime, Iter]
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
        
    def process(self, chain, processing, modelExtraProcessing, invoker:Invoker, create:Create, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the model encoder.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypeModel): return
        # The type is not for a model, nothing to do, just move along
        assert isinstance(create.objType, TypeModel)
        
        if Create.name in create and create.name: name = create.name
        else: name = create.objType.name
        if Create.specifiers in create: specifiers = create.specifiers or ()
        else: specifiers = ()
        
        properties, extra = [], None
        if not invoker.hideProperties:
            for prop in self.sortedTypes(create.objType):
                assert isinstance(prop, TypeProperty), 'Invalid property type %s' % prop
                arg = processing.executeWithAll(create=processing.ctx.create(objType=prop, name=prop.name),
                                                invoker=invoker, **keyargs)
                assert isinstance(arg.create, CreateProperty), 'Invalid create property %s' % arg.create
                if arg.create.encoder is None:
                    if Create.isCorrupted in create: create.isCorrupted = True
                    log.error('Cannot encode %s', prop)
                    return chain.cancel()
                properties.append((prop.name, arg.create.encoder))
        
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
        sorted = list(model.properties.values())
        if model.propertyId: sorted.remove(model.propertyId)
        sorted.sort(key=lambda prop: prop.name)
        sorted.sort(key=self.sortKey)
        if model.propertyId: sorted.insert(0, model.propertyId)
        return sorted
    
    def sortKey(self, prop):
        '''
        Provides the sorting key for property types, used in sort functions.
        '''
        assert isinstance(prop, TypeProperty), 'Invalid property type %s' % prop

        for k, ord in enumerate(self.typeOrders):
            if prop.type == ord: break
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
        
    def encode(self, obj, target, support):
        '''
        @see: IEncoder.encode
        '''
        assert isinstance(target, IRender), 'Invalid target %s' % target
        
        if not self.properties:
            target.beginObject(self.name, **self.populate(obj, support, indexBlock=NAME_BLOCK))
        else:
            target.beginObject(self.name, **self.populate(obj, support))
            for name, encoder in self.properties:
                assert isinstance(encoder, IEncoder), 'Invalid property encoder %s' % encoder
                objValue = getattr(obj, name)
                if objValue is None: continue
                encoder.encode(objValue, target, support)
                
            if self.extra: self.extra.encode(obj, target, support)
                
        target.end()
