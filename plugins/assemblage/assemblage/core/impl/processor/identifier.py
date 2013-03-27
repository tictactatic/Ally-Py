'''
Created on Mar 26, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the identifiers or identifier data.
'''

from ally.api.config import GET, INSERT
from ally.api.operator.type import TypeModelProperty
from ally.api.type import Type, TypeReference
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Invoker, INodeChildListener, \
    INodeInvokerListener, Node, Path
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, HandlerProcessor
from ally.http.spec.server import HTTP_GET, HTTP_POST, IEncoderPath
from ally.support.core.util_resources import iterateNodes, METHOD_NODE_ATTRIBUTE, \
    hashForNode, pathForNode
from assemblage.api.assemblage import Identifier
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
    objType = defines(Type, doc='''
    @rtype: Type
    The object type represented by the response.
    ''')
    result = defines(Iterable, doc='''
    @rtype: Iterable(Identifier)
    The generated identifiers.
    ''')
    # ---------------------------------------------------------------- Required
    identifierId = requires(int)
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
    # ---------------------------------------------------------------- Required
    encoderPath = requires(IEncoderPath)
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='provideIdentifiers')
class ProvideIdentifiers(HandlerProcessor, INodeChildListener, INodeInvokerListener):
    '''
    Provides the identifiers or identifier support.
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
        
        if obtain.required == Identifier:
            assert isinstance(support.encoderPath, IEncoderPath), 'Invalid encoder path %s' % support.encoderPath
            identifiers = self.processIdentifiers(support.encoderPath)
            if obtain.result is None: obtain.result = identifiers
            else: obtain.result = itertools.chain(obtain.result, identifiers)
            return
        
        assert obtain.identifierId, 'A structure id is required'
        structure = self.identifiersById().get(obtain.identifierId)
        if structure:
            node, _method, obtain.objType = structure
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
        
    def identifiersById(self):
        '''
        Provides the nodes and identifiers indexed by hashed id.
        '''
        if self._cache is None:
            
            self._cache = {}
            for node in iterateNodes(self.resourcesRoot):
                assert isinstance(node, Node), 'Invalid node %s' % node
    
                for method, attr in METHOD_NODE_ATTRIBUTE.items():
                    name = TO_METHOD_NAME.get(method)
                    if name is None: continue
                    # If not the right method then just ignore it.
                    invoker = getattr(node, attr)
                    if not invoker: continue
                    assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
                    
                    typ = objType = invoker.output
                    if isinstance(typ, TypeModelProperty): typ = typ.type
                    if isinstance(typ, TypeReference): continue
                    # We need to exclude the references representations because this are automatically redirected to, 
                    # @see: redirect processor from ally-core-http component.
                    
                    self._cache[hash((hashForNode(node), method)) & 0x7FFFFFF] = (node, name, objType)
        
        return self._cache
    
    def processIdentifiers(self, encoderPath):
        '''
        Process the identifiers.
        '''
        assert isinstance(encoderPath, IEncoderPath), 'Invalid encoder path %s' % encoderPath
        for identifierId, (node, method, _type) in self.identifiersById().items():
            identifier = Identifier()
            identifier.Id = identifierId
            identifier.Method = method
            identifier.Pattern = '%s[\\/]?(?:\\.|$)' % encoderPath.encodePattern(pathForNode(node), invalid=self.replace)
            
            yield identifier
    
    def replace(self, match, converterPath):
        '''
        Method used for replacing within the pattern path.
        '''
        return '[^\\/]+'
