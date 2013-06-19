'''
Created on Mar 18, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the model property encoder.
'''

from ally.api.operator.type import TypeModel, TypeProperty
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IEncoder, EncoderWithSpecifiers, \
    IRender
from ally.core.spec.transform.index import NAME_BLOCK
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional
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
        super().__init__(Branch(self.propertyEncodeAssembly).included().using(create=CreateProperty))
        
    def process(self, chain, propertyProcessing, invoker:Invoker, create:Create, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the model property encoder.
        '''
        assert isinstance(propertyProcessing, Processing), 'Invalid processing %s' % propertyProcessing
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        prop = create.objType
        if not isinstance(prop, TypeProperty): return
        # The type is not for a property, nothing to do, just move along
        assert isinstance(prop, TypeProperty)
        if not isinstance(prop.parent, TypeModel): return
        # The type is not for a model, nothing to do, just move along
        assert isinstance(prop.parent, TypeModel)
        
        if Create.name in create and create.name: name = create.name
        else: name = prop.parent.name
        if Create.specifiers in create: specifiers = create.specifiers or ()
        else: specifiers = ()
        
        if not invoker.hideProperties:
            arg = propertyProcessing.execute(create=propertyProcessing.ctx.create(objType=prop, name=prop.name), **keyargs)
            assert isinstance(arg.create, CreateProperty), 'Invalid create property %s' % arg.create
            if arg.create.encoder is None: raise DevelError('Cannot encode %s' % prop)
            encoder = arg.create.encoder
        else: encoder = None
        
        create.encoder = EncoderModelProperty(name, encoder, specifiers)
        
# --------------------------------------------------------------------

class EncoderModelProperty(EncoderWithSpecifiers):
    '''
    Implementation for a @see: IEncoder for model property.
    '''
    
    def __init__(self, name, encoder, specifiers=None):
        '''
        Construct the model property encoder.
        '''
        assert isinstance(name, str), 'Invalid model name %s' % name
        assert encoder is None or isinstance(encoder, IEncoder), 'Invalid property encoder %s' % encoder
        super().__init__(specifiers)
        
        self.name = name
        self.encoder = encoder
        
    def encode(self, obj, target, support):
        '''
        @see: IEncoder.encode
        '''
        assert isinstance(target, IRender), 'Invalid target %s' % target
        
        target.beginObject(self.name, **self.populate(obj, support, indexBlock=NAME_BLOCK))
        if self.encoder: self.encoder.encode(obj, target, support)
        target.end()
