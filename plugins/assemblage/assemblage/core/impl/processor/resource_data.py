'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invokers handlers for assemblages.
'''

from ally.api.config import GET, INSERT
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Invoker, INodeChildListener, \
    INodeInvokerListener, Node
from ally.design.processor.attribute import defines, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, HandlerProcessor
from ally.support.core.util_resources import iterateNodes, METHOD_NODE_ATTRIBUTE, \
    hashForNode
from collections import Iterable
import itertools

# --------------------------------------------------------------------

AVAILABLE_METHODS = {GET, INSERT}
# The available methods for assemblages.
                    
# --------------------------------------------------------------------
    
class DataAssemblageResource(Context):
    '''
    The data assemblage context.
    '''
    # ---------------------------------------------------------------- Defined
    id = defines(int, doc='''
    @rtype: integer
    The unique id for data.
    ''')
    node = defines(Node, doc='''
    @rtype: Node
    The node that has the invoker.
    ''')
    invoker = defines(Invoker, doc='''
    @rtype: Node
    The invoker.
    ''')
    
class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Optional
    assemblageId = optional(int)
    # ---------------------------------------------------------------- Defined
    assemblages = defines(Iterable, doc='''
    @rtype: Iterable(DataAssemblage)
    The data's if no assemblage id is provided.
    ''')

# --------------------------------------------------------------------

@injected
@setup(Handler, name='iterateResourceData')
class IterateResourceData(HandlerProcessor, INodeChildListener, INodeInvokerListener):
    '''
    Iterated the data populated with tree resources.
    '''
    
    resourcesRoot = Node; wire.entity('resourcesRoot')
    # The root node to process the repository against.
    
    def __init__(self):
        assert isinstance(self.resourcesRoot, Node), 'Invalid root node %s' % self.resourcesRoot
        super().__init__()
        
        self._cache = None
        self.resourcesRoot.addStructureListener(self)
        
    def process(self, chain, DataAssemblage:DataAssemblageResource, obtain:Obtain, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Iterates the data with tree resources or provides the data for the assemblage id.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert issubclass(DataAssemblage, DataAssemblageResource), 'Invalid data class %s' % DataAssemblage
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        
        if Obtain.assemblageId not in obtain or obtain.assemblageId is None:
            assemblages = (DataAssemblage(id=id, node=node, invoker=invoker)
                           for id, (node, invoker) in self.invokers().items())
        else:
            data = self.invokers().get(obtain.assemblageId)
            if data is None: return  # We cannot proceed without a data for the assemblage id
            node, invoker = data
            assemblages = (DataAssemblage(id=obtain.assemblageId, node=node, invoker=invoker),)
            
        if obtain.assemblages is None: obtain.assemblages = assemblages
        else: obtain.assemblages = itertools.chain(obtain.assemblages, assemblages)
            
        chain.proceed()
        
    # ----------------------------------------------------------------
        
    def onChildAdded(self, node, child):
        '''
        @see: INodeChildListener.onChildAdded
        '''
        self._cache = None
    
    def onInvokerChange(self, node, old, new):
        '''
        @see: INodeInvokerListener.onInvokerChange
        '''
        self._cache = None
        
    # ----------------------------------------------------------------
        
    def invokers(self):
        '''
        Provides the nodes and invokers indexed by hashed id.
        '''
        if self._cache is None:
            self._cache = {}
            for node in iterateNodes(self.resourcesRoot):
                assert isinstance(node, Node), 'Invalid node %s' % node
    
                for method, attr in METHOD_NODE_ATTRIBUTE.items():
                    if method not in AVAILABLE_METHODS: continue
                    invoker = getattr(node, attr)
                    if not invoker: continue
                    self._cache[hash((hashForNode(node), method)) & 0x7FFFFFF] = (node, invoker)
        return self._cache
