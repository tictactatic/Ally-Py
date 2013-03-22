'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the data resource invoker encoder.
'''

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
from collections import Iterable
import logging
from assemblage.api.assemblage import Target, Matcher, Adjuster
    
# --------------------------------------------------------------------

log = logging.getLogger(__name__)
               
# --------------------------------------------------------------------
    
class DataResource(Context):
    '''
    The data context.
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
    datas = requires(Iterable)

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
    
    def process(self, encodeProcessing, Data:DataResource, obtain:Obtain, support:Context, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Provides the encoders for the data elements.
        '''
        assert isinstance(encodeProcessing, Processing), 'Invalid processing %s' % encodeProcessing
        assert issubclass(Data, DataResource), 'Invalid data class %s' % Data
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(obtain.datas, Iterable), 'Invalid datas %s' % obtain.datas
        
        if obtain.required not in (Target, Matcher, Adjuster): return  # The required type doesn't need representations 
        
        obtain.datas = self.populateRepresentations(obtain.datas, encodeProcessing, support)
        
    # ----------------------------------------------------------------
        
    def populateRepresentations(self, datas, proc, support):
        '''
        Provides the representation data.
        '''
        assert isinstance(datas, Iterable), 'Invalid datas %s' % datas
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        for data in datas:
            assert isinstance(data, DataResource), 'Invalid data %s' % data
            assert isinstance(data.invoker, Invoker), 'Invalid data invoker %s' % data.invoker
            
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
