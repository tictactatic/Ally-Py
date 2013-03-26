'''
Created on Mar 22, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the structures ids and structures datas.
'''

from ally.api.config import GET, INSERT
from ally.api.operator.type import TypeModelProperty, TypeModel
from ally.api.type import Type, TypeReference, Iter
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Invoker, INodeChildListener, \
    INodeInvokerListener, Node, Path
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, HandlerProcessor
from ally.http.spec.server import HTTP_GET, HTTP_POST
from ally.support.core.util_resources import iterateNodes, METHOD_NODE_ATTRIBUTE, \
    hashForNode, pathForNode, findGetModel
from assemblage.api.assemblage import Structure
from collections import Iterable
import itertools

# --------------------------------------------------------------------

TO_METHOD_NAME = {GET: HTTP_GET, INSERT: HTTP_POST}
# The mapping from configuration methods to http methods.
                    
# --------------------------------------------------------------------

class Obtain(Context):
    '''
    The data obtain context.
    '''
    # ---------------------------------------------------------------- Defined
    method = defines(str, doc='''
    @rtype: string
    The method name associated with the node.
    ''')
    objType = defines(Type, doc='''
    @rtype: Type
    The object type represented by the response.
    ''')
    result = defines(object, doc='''
    @rtype: Iterable(integer)
    The generated structure ids.
    ''')
    # ---------------------------------------------------------------- Required
    structureId = requires(int)
    required = requires(object)

class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(Path, doc='''
    @rtype: Path
    The path that is targeted.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideStructuresIds')
class ProvideStructuresIds(HandlerProcessor, INodeChildListener, INodeInvokerListener):
    '''
    Provides the structure id's or structure support.
    '''
    
    resourcesRoot = Node; wire.entity('resourcesRoot')
    # The root node to process the repository against.
    
    def __init__(self):
        assert isinstance(self.resourcesRoot, Node), 'Invalid root node %s' % self.resourcesRoot
        super().__init__()
        
        self._cache = None
        self.resourcesRoot.addStructureListener(self)
        
    def process(self, chain, obtain:Obtain, support:Support, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Iterates the data with tree resources or provides the data for the assemblage id.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(obtain, Obtain), 'Invalid obtain request %s' % obtain
        assert isinstance(support, Support), 'Invalid support %s' % support
        
        if obtain.required == Structure.Id:
            if obtain.result is None: obtain.result = self.structures().keys()
            else:
                assert isinstance(obtain.result, Iterable), 'Cannot merge with result %s' % obtain.result
                obtain.result = itertools.chain(obtain.result, self.structures().keys())
            return
        
        assert obtain.structureId, 'A structure id is required'
        
        structure = self.structures().get(obtain.structureId)
        if structure:
            node, obtain.method, obtain.objType = structure
            if node: support.path = pathForNode(node)
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
        
    def structures(self):
        '''
        Provides the nodes and structures indexed by hashed id.
        '''
        if self._cache is None:
            
            self._cache = {}
            for node in iterateNodes(self.resourcesRoot):
                assert isinstance(node, Node), 'Invalid node %s' % node
    
                for method, attr in METHOD_NODE_ATTRIBUTE.items():
                    methodName = TO_METHOD_NAME.get(method)
                    if methodName is None: continue
                    # If not the right method then just ignore it.
                    invoker = getattr(node, attr)
                    if not invoker: continue
                    assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
                    self.processInStructure(node, methodName, invoker.output)
                    
        return self._cache

    def processInStructure(self, node, method, objType):
        '''
        Process in structure the provided data.
        '''
        typ = objType
        if isinstance(typ, TypeModelProperty): typ = typ.type
        if isinstance(typ, TypeReference): return
        # We need to exclude the references representations because this are automatically redirected to, 
        # @see: redirect processor from ally-core-http component.
        
        if node: hashId = hash((hashForNode(node), method, None)) & 0x7FFFFFF
        else: hashId = hash((None, method, objType)) & 0x7FFFFFF
        if hashId in self._cache: return
        # The hash is already present, no need to process.
        
        self._cache[hashId] = (node, method, objType)
        
        if isinstance(objType, Iter):
            # If we have a collection of models then we need to create also a structure for the item if there
            # is not one yet.
            assert isinstance(objType, Iter)
            if isinstance(objType.itemType, TypeModel):
                if node:
                    itemPath = findGetModel(pathForNode(node), objType.itemType)
                    if itemPath:
                        assert isinstance(itemPath, Path), 'Invalid path %s' % itemPath
                        self.processInStructure(itemPath.node, TO_METHOD_NAME[GET], objType.itemType)
                        return
                    
                self.processInStructure(None, None, objType.itemType)
        
