'''
Created on Mar 7, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the model encoder.
'''

from .base import RequestEncoderNamed, RequestEncoder, DefineEncoder, \
    encoderSpecifiers, encoderName
from ally.api.operator.type import TypeModel, TypeProperty
from ally.api.type import Iter, Boolean, Integer, Number, String, Time, Date, \
    DateTime, typeFor
from ally.container.ioc import injected
from ally.core.impl.index import NAME_BLOCK
from ally.core.impl.transform import TransfromWithSpecifiers
from ally.core.spec.transform import ITransfrom, IRender
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Abort
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
        super().__init__(Branch(self.propertyEncodeAssembly).included().using(create=RequestEncoderNamed),
                         Branch(self.modelExtraEncodeAssembly).included().using(create=RequestEncoder))
        
        self.typeOrders = [typeFor(typ) for typ in self.typeOrders]
        
    def process(self, chain, processing, modelExtraProcessing, invoker:Invoker, create:DefineEncoder, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the model encoder.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, DefineEncoder), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypeModel): return
        # The type is not for a model, nothing to do, just move along
        assert isinstance(create.objType, TypeModel)
        
        extra, properties = None, []
        if not invoker.hideProperties:
            for prop in self.sortedTypes(create.objType):
                assert isinstance(prop, TypeProperty), 'Invalid property type %s' % prop
                arg = processing.executeWithAll(create=processing.ctx.create(objType=prop, name=prop.name),
                                                invoker=invoker, **keyargs)
                assert isinstance(arg.create, RequestEncoderNamed), 'Invalid create property %s' % arg.create
                if arg.create.encoder is None:
                    log.error('Cannot encode %s', prop)
                    raise Abort(create)
                properties.append((prop.name, arg.create.encoder))
        
            if modelExtraProcessing:
                assert isinstance(modelExtraProcessing, Processing), 'Invalid processing %s' % modelExtraProcessing
                arg = modelExtraProcessing.execute(create=modelExtraProcessing.ctx.create(objType=create.objType),
                                                   invoker=invoker, **keyargs)
                assert isinstance(arg.create, RequestEncoder), 'Invalid create model extra %s' % arg.create
                extra = arg.create.encoder
            
        create.encoder = EncoderModel(encoderName(create, create.objType.name), properties, extra, encoderSpecifiers(create))

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

class EncoderModel(TransfromWithSpecifiers):
    '''
    Implementation for a @see: ITransfrom for model.
    '''
    
    def __init__(self, name, properties, extra=None, specifiers=None):
        '''
        Construct the model encoder.
        '''
        assert isinstance(name, str), 'Invalid model name %s' % name
        assert isinstance(properties, list), 'Invalid properties %s' % properties
        assert extra is None or isinstance(extra, ITransfrom), 'Invalid extra encoder %s' % extra
        super().__init__(specifiers)
        
        self.name = name
        self.properties = properties
        self.extra = extra
        
    def transform(self, value, target, support):
        '''
        @see: ITransfrom.transform
        '''
        assert isinstance(target, IRender), 'Invalid target %s' % target
        
        if not self.properties:
            target.beginObject(self.name, **self.populate(value, support, indexBlock=NAME_BLOCK))
        else:
            target.beginObject(self.name, **self.populate(value, support))
            for name, encoder in self.properties:
                assert isinstance(encoder, ITransfrom), 'Invalid property encoder %s' % encoder
                val = getattr(value, name)
                if val is None: continue
                encoder.transform(val, target, support)
                
            if self.extra: self.extra.transform(value, target, support)
                
        target.end()
