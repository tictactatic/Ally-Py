'''
Created on Jul 27, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoker encoder.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.spec.transform.encoder import IEncoder
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
import logging
from ally.api.operator.type import TypeModelProperty

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder to be used for rendering the response object.
    ''')
    hideProperties = defines(bool, doc='''
    @rtype: boolean
    Indicates that the properties of model rendering should be hidden (not rendering).
    ''')
    # ---------------------------------------------------------------- Required
    node = requires(Context)
    output = requires(Type)
    isCollection = requires(bool)
    invokerGet = requires(Context)

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    objType = defines(object, doc='''
    @rtype: object
    The object type.
    ''')
    # ---------------------------------------------------------------- Required
    encoder = requires(IEncoder)
    
# --------------------------------------------------------------------

@injected
class EncodingHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the creation of encoders for response objects.
    '''
    
    encodeAssembly = Assembly
    # The encode processors to be used for encoding properties.
    
    def __init__(self):
        assert isinstance(self.encodeAssembly, Assembly), 'Invalid encode assembly %s' % self.encodeAssembly
        super().__init__(Branch(self.encodeAssembly).using(create=Create).
                         included(('invoker', 'Invoker'), ('node', 'Node')).included(), Invoker=Invoker)

    def process(self, chain, encodeProcessing, register:Register, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Process the encoder rendering.
        '''
        assert isinstance(encodeProcessing, Processing), 'Invalid processing %s' % encodeProcessing
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return  # No invokers to process.
        
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            if invoker.invokerGet:
                if invoker.isCollection:
                    # TODO: Gabriel: This is a temporary fix to get the same rendering as before until we refactor the plugins
                    # to return only ids.
                    invoker.hideProperties = True
                elif isinstance(invoker.output, TypeModelProperty):
                    assert isinstance(invoker.output, TypeModelProperty)
                    if invoker.output.isId(): invoker.hideProperties = True
            
            arg = encodeProcessing.executeWithAll(create=encodeProcessing.ctx.create(objType=invoker.output),
                                                  node=invoker.node, invoker=invoker, **keyargs)
            assert isinstance(arg.create, Create), 'Invalid create %s' % arg.create
            if arg.create.encoder is not None: invoker.encoder = arg.create.encoder
