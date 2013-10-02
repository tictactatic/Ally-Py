'''
Created on Jul 27, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoker encoder.
'''

from ally.api.type import Type, Iter
from ally.container.ioc import injected
from ally.core.spec.transform import ITransfrom
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Abort, FILL_ALL
from ally.design.processor.handler import HandlerBranching
from ally.support.api.util_service import isModelId
import logging

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
    encoder = defines(ITransfrom, doc='''
    @rtype: ITransfrom
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
    location = requires(str)

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    objType = defines(Type, doc='''
    @rtype: Type
    The type that is the target of the encoder create.
    ''')
    # ---------------------------------------------------------------- Required
    encoder = requires(ITransfrom)
    
# --------------------------------------------------------------------

@injected
class EncodingHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the creation of encoders for invokers.
    '''
    
    encodeAssembly = Assembly
    # The encode processors to be used for encoding properties.
    
    def __init__(self):
        assert isinstance(self.encodeAssembly, Assembly), 'Invalid encode assembly %s' % self.encodeAssembly
        super().__init__(Branch(self.encodeAssembly).using(create=Create).
                         included(('invoker', 'Invoker'), ('node', 'Node')).included(),
                         Invoker=Invoker)

    def process(self, chain, processing, register:Register, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Populate the encoder.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return
        
        aborted = []
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            assert invoker.node, 'Invalid invoker %s with no node' % invoker
            
            if invoker.invokerGet:
                if invoker.isCollection:
                    assert isinstance(invoker.output, Iter), 'Invalid output %s' % invoker.output
                    if isModelId(invoker.output.itemType): invoker.hideProperties = True
                elif isModelId(invoker.output): invoker.hideProperties = True
            
            try: arg = processing.execute(FILL_ALL, create=processing.ctx.create(objType=invoker.output),
                                          node=invoker.node, invoker=invoker, **keyargs)
            except Abort:
                log.error('Cannot use because cannot create encoder for %s, at:%s', invoker.output, invoker.location)
                aborted.append(invoker)
            else:
                assert isinstance(arg.create, Create), 'Invalid create %s' % arg.create
                if arg.create.encoder is not None: invoker.encoder = arg.create.encoder
                
        if aborted: raise Abort(*aborted)
