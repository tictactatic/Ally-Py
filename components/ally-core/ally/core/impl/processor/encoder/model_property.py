'''
Created on Mar 18, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the model property encoder.
'''

from .base import RequestEncoderNamed, DefineEncoder, encoderSpecifiers, encoderName
from ally.api.operator.type import TypeModel, TypeProperty
from ally.container.ioc import injected
from ally.core.impl.transform import TransfromWithSpecifiers
from ally.core.spec.transform import ITransfrom, IRender
from ally.core.impl.index import NAME_BLOCK
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
class ModelPropertyEncode(HandlerBranching):
    '''
    Implementation for a handler that provides the model property encoding.
    '''
    
    propertyEncodeAssembly = Assembly
    # The encode processors to be used for encoding properties.
    
    def __init__(self):
        assert isinstance(self.propertyEncodeAssembly, Assembly), \
        'Invalid property encode assembly %s' % self.propertyEncodeAssembly
        super().__init__(Branch(self.propertyEncodeAssembly).included().using(create=RequestEncoderNamed))
        
    def process(self, chain, processing, invoker:Invoker, create:DefineEncoder, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the model property encoder.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, DefineEncoder), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        prop = create.objType
        if not isinstance(prop, TypeProperty): return
        # The type is not for a property, nothing to do, just move along
        assert isinstance(prop, TypeProperty)
        if not isinstance(prop.parent, TypeModel): return
        # The type is not for a model, nothing to do, just move along
        assert isinstance(prop.parent, TypeModel)
        
        if not invoker.hideProperties:
            arg = processing.executeWithAll(create=processing.ctx.create(objType=prop, name=prop.name), **keyargs)
            assert isinstance(arg.create, RequestEncoderNamed), 'Invalid create property %s' % arg.create
            if arg.create.encoder is None:
                log.error('Cannot encode %s', prop)
                raise Abort(create)
            encoder = arg.create.encoder
        else: encoder = None
        
        create.encoder = EncoderModelProperty(encoderName(create, prop.parent.name), encoder, encoderSpecifiers(create))
        
# --------------------------------------------------------------------

class EncoderModelProperty(TransfromWithSpecifiers):
    '''
    Implementation for a @see: ITransfrom for model property.
    '''
    
    def __init__(self, name, encoder, specifiers=None):
        '''
        Construct the model property encoder.
        '''
        assert isinstance(name, str), 'Invalid model name %s' % name
        assert encoder is None or isinstance(encoder, ITransfrom), 'Invalid property encoder %s' % encoder
        super().__init__(specifiers)
        
        self.name = name
        self.encoder = encoder
        
    def transform(self, value, target, support):
        '''
        @see: ITransfrom.transform
        '''
        assert isinstance(target, IRender), 'Invalid target %s' % target
        
        target.beginObject(self.name, **self.populate(value, support, indexBlock=NAME_BLOCK))
        if self.encoder: self.encoder.transform(value, target, support)
        target.end()
