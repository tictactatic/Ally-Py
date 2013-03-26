'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the data resource invoker encoder.
'''

from ally.api.operator.type import TypeModelProperty
from ally.api.type import TypeReference
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Invoker, Node, Path
from ally.core.spec.transform.encoder import IEncoder
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.branch import Using
from ally.design.processor.context import Context, pushIn
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import Handler, HandlerBranchingProceed
from ally.support.core.util_resources import pathForNode
from assemblage.api.assemblage import Matcher
from collections import Iterable
import logging
    
# --------------------------------------------------------------------

log = logging.getLogger(__name__)
               
# --------------------------------------------------------------------
    
class DataAssemblageResource(Context):
    '''
    The data assemblage context.
    '''
    # ---------------------------------------------------------------- Defined
    representation = defines(object, doc='''
    @rtype: object
    The representation object for the invoker output.
    ''')
    # ---------------------------------------------------------------- Required
    node = requires(Node)
    invoker = requires(Invoker)
    
class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Required
    required = requires(type)
    assemblages = requires(Iterable)

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

class SupportEncoder(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(Path, doc='''
    @rtype: Path
    The path used by the encoders.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideRepresentation')
class ProvideRepresentation(HandlerBranchingProceed):
    '''
    Provides the representation for the resource data.
    '''
    
    assemblyEncode = Assembly; wire.entity('assemblyEncode')
    # The encode processors to be used for encoding properties.
    
    def __init__(self):
        assert isinstance(self.assemblyEncode, Assembly), 'Invalid encode assembly %s' % self.assemblyEncode
        super().__init__(Using(self.assemblyEncode, 'support', create=CreateEncoder, support=SupportEncoder))
    
    def process(self, encodeProcessing, DataAssemblage:DataAssemblageResource, obtain:Obtain, support:Context, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Provides the encoders for the data elements.
        '''
        assert isinstance(encodeProcessing, Processing), 'Invalid processing %s' % encodeProcessing
        assert issubclass(DataAssemblage, DataAssemblageResource), 'Invalid data class %s' % DataAssemblage
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(obtain.assemblages, Iterable), 'Invalid assemblages %s' % obtain.assemblages
        
        provide = obtain.required == Matcher  # The required type needs representations 
        obtain.assemblages = self.processAssemblages(obtain.assemblages, encodeProcessing, support, provide)
        
    # ----------------------------------------------------------------
        
    def processAssemblages(self, datas, proc, support, provide):
        '''
        Provides the representation data or trims data that is not useful for representations.
        '''
        assert isinstance(datas, Iterable), 'Invalid datas %s' % datas
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        assert isinstance(provide, bool), 'Invalid provide representation flag %s' % provide
        for data in datas:
            assert isinstance(data, DataAssemblageResource), 'Invalid data %s' % data
            assert isinstance(data.invoker, Invoker), 'Invalid data invoker %s' % data.invoker
            
            typ = data.invoker.output
            if isinstance(typ, TypeModelProperty): typ = typ.type
            if isinstance(typ, TypeReference): continue
            # We need to exclude the references representations because this are automatically redirected to, @see: redirect
            # processor from ally-core-http component.
            
            if not provide:
                yield data
                continue
            
            create = proc.ctx.create(objType=data.invoker.output)
            support = pushIn(proc.ctx.support(), support)
            assert isinstance(support, SupportEncoder), 'Invalid support %s' % support
            support.path = pathForNode(data.node)
            
            chain = Chain(proc)
            chain.process(create=create, support=support).doAll()
            create, support = chain.arg.create, chain.arg.support
            assert isinstance(create, CreateEncoder), 'Invalid create %s' % create
            if create.encoder is None:
                log.error('No encoder available for %s in \'%s\'', data.invoker.output, support.path)
                continue  # No encoder available, so we skip this data
            assert isinstance(create.encoder, IEncoder), 'Invalid encoder %s' % create.encoder
            
            data.representation = create.encoder.represent(support)
            
            yield data
