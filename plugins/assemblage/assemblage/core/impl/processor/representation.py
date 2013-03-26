'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the object type representation.
'''

from ally.api.type import Type
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.transform.encoder import IEncoder
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.branch import Using
from ally.design.processor.context import Context, pushIn
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import Handler, HandlerBranching
import logging
    
# --------------------------------------------------------------------

log = logging.getLogger(__name__)
               
# --------------------------------------------------------------------
    
class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Defined
    representation = defines(object, doc='''
    @rtype: object
    The representation object for the invoker output.
    ''')
    # ---------------------------------------------------------------- Required
    objType = requires(Type)

class CreateEncoder(Context):
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
@setup(Handler, name='provideRepresentation')
class ProvideRepresentation(HandlerBranching):
    '''
    Provides the representation for the resource data.
    '''
    
    assemblyEncode = Assembly; wire.entity('assemblyEncode')
    # The encode processors to be used for encoding properties.
    
    def __init__(self):
        assert isinstance(self.assemblyEncode, Assembly), 'Invalid encode assembly %s' % self.assemblyEncode
        super().__init__(Using(self.assemblyEncode, 'support', create=CreateEncoder))
    
    def process(self, chain, encodeProcessing, obtain:Obtain, support:Context, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Provides the representation for object type.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(encodeProcessing, Processing), 'Invalid processing %s' % encodeProcessing
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(obtain.objType, Type), 'Invalid obtain object type %s' % obtain.objType
        
        create = encodeProcessing.ctx.create(objType=obtain.objType)
        support = pushIn(encodeProcessing.ctx.support(objType=obtain.objType), support)
        encodeChain = Chain(encodeProcessing)
        encodeChain.process(create=create, support=support).doAll()
        create, support = encodeChain.arg.create, encodeChain.arg.support
        assert isinstance(create, CreateEncoder), 'Invalid create %s' % create
        if create.encoder is None:
            log.error('No encoder available for %s', obtain.objType)
            return  # No encoder available, so we skip this data
        assert isinstance(create.encoder, IEncoder), 'Invalid encoder %s' % create.encoder
        
        obtain.representation = create.encoder.represent(support)
        chain.proceed()
