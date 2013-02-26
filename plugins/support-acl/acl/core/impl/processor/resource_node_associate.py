'''
Created on Feb 21, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that associates a resources node with ACL rights.
'''

from acl.right_sevice import Structure, StructMethod, StructService, StructCall, \
    RightService
from acl.spec import Filter, RightAcl
from ally.api.operator.container import Call
from ally.api.type import typeFor
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.impl.invoker import InvokerCall
from ally.core.spec.resources import Invoker, INodeChildListener, \
    INodeInvokerListener, Path, Node
from ally.design.bean import Bean, Attribute
from ally.design.processor.attribute import defines, requires, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed, Handler
from ally.support.core.util_resources import iterateNodes, pathForNode, \
    METHOD_NODE_ATTRIBUTE, invokerCallOf
from collections import Iterable
from itertools import chain

# --------------------------------------------------------------------

@injected
@setup(name='repositoryNodeService')
class RepositoryNodeService(INodeChildListener, INodeInvokerListener):
    '''
    Provides the cached services for the association of a resource node with ACL rights.
    '''
    
    resourcesRoot = Node; wire.entity('resourcesRoot')
    # The root node to process the repository against.
    
    def __init__(self):
        assert isinstance(self.resourcesRoot, Node), 'Invalid root node %s' % self.resourcesRoot
        
        self._structures = {}
    
    def onChildAdded(self, node, child):
        '''
        @see: INodeChildListener.onChildAdded
        '''
        self._structures.clear()
    
    def onInvokerChange(self, node, old, new):
        '''
        @see: INodeInvokerListener.onInvokerChange
        '''
        self._structures.clear()
        
    # ----------------------------------------------------------------
    
    def process(self, structure):
        '''
        Process the structure for the node.
        
        @param structure: Structure
            The structure to process a node structure for.
        @return: StructNode
            The node structure.
        '''
        assert isinstance(structure, Structure), 'Invalid structure %s' % structure
        structureId = id(structure)
        structNode = self._structures.get(structureId)
        if not structNode:
            structNode = self._structures[structureId] = StructNode()
            for node in iterateNodes(self.resourcesRoot):
                assert isinstance(node, Node), 'Invalid node %s' % node
    
                for method, attr in METHOD_NODE_ATTRIBUTE.items():
                    original = getattr(node, attr)
                    if not original: continue
                    invoker = invokerCallOf(original)
                    if not invoker: continue
                    
                    assert isinstance(invoker, InvokerCall)
                    assert isinstance(invoker.call, Call)
                    
                    structMethod = structure.methods.get(method)
                    if not structMethod: continue
                    assert isinstance(structMethod, StructMethod)
                    
                    structService = structMethod.services.get(typeFor(invoker.implementation))
                    if not structService: continue
                    assert isinstance(structService, StructService)
                    
                    structCall = structService.calls.get(invoker.call.name)
                    if not structCall: continue
                    assert isinstance(structCall, StructCall)
                    
                    structNodeInvokers = structNode.calls.get(structCall)
                    if not structNodeInvokers: structNodeInvokers = structNode.calls[structCall] = StructNodeInvokers()
                    
                    nodeId = id(node)
                    structInvoker = structNodeInvokers.invokers.get(nodeId)
                    if not structInvoker: structNodeInvokers.invokers[nodeId] = StructInvoker(invoker=original, node=node)
        return structNode

# --------------------------------------------------------------------

class Solicitation(Context):
    '''
    The solicitation context.
    '''
    # ---------------------------------------------------------------- Optional
    method = optional(int, doc='''
    @rtype: integer
    The method to get the permissions one of (GET, INSERT, UPDATE, DELETE) or a combination of those using the
    "|" operator, if None then all methods are considered.
    ''')
    # ---------------------------------------------------------------- Required
    rights = requires(Iterable, doc='''
    @rtype: Iterable(RightAcl)
    The rights that make the scope of the resource node association, this iterable gets trimmed of all processed rights.
    ''')

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    rightsAvailable = defines(Iterable, doc='''
    @rtype: Iterable(RightAcl)
    The rights that are available.
    ''')

class PermissionResource(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Defined
    method = defines(int, doc='''
    @rtype: integer
    The method of the permission.
    ''')
    path = defines(Path, doc='''
    @rtype: Path
    The path of the permission.
    ''')
    invoker = defines(Invoker, doc='''
    @rtype: Invoker
    The invoker of the permission.
    ''')
    filters = defines(list, doc='''
    @rtype: list[Filter]
    The filters for the permission.
    ''')

class SolicitationWithPermissions(Solicitation):
    '''
    The solicitation context with permissions.
    '''
    # ---------------------------------------------------------------- Optional
    node = optional(Node, doc='''
    @rtype: Node
    The node to get the permissions for, if there is no None then the entire tree structure is used.
    ''')
    # ---------------------------------------------------------------- Defined
    permissions = defines(Iterable, doc='''
    @rtype: Iterable(Permission)
    The solicitation permissions.
    ''')

# --------------------------------------------------------------------

@injected
@setup(Handler, name='checkResourceAvailableRights')
class CheckResourceAvailableRights(HandlerProcessorProceed):
    '''
    Provides the handler that filters the rights and keeps only those that have permissions.
    '''
    
    repositoryNodeService = RepositoryNodeService; wire.entity('repositoryNodeService')
    # The repository node service to use for extracting the node structures.

    def __init__(self):
        assert isinstance(self.repositoryNodeService, RepositoryNodeService), \
        'Invalid repository node service %s' % self.repositoryNodeService
        super().__init__()

    def process(self, solicitation:Solicitation, reply:Reply, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Filters the rights with permissions.
        '''
        assert isinstance(solicitation, Solicitation), 'Invalid solicitation %s' % solicitation
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        assert isinstance(solicitation.rights, Iterable), 'Invalid rights %s' % solicitation.rights
        
        serviceRights, unprocessed = [], []
        for right in solicitation.rights:
            if isinstance(right, RightService):
                assert isinstance(right, RightService)
                serviceRights.append(right)
            else:
                assert isinstance(right, RightAcl), 'Invalid right %s' % right
                unprocessed.append(right)
            
        solicitation.rights = unprocessed
        
        available = self.iterAvailableRights(serviceRights, solicitation.method)
        if Reply.rightsAvailable in reply:
            reply.rightsAvailable = chain(reply.rightsAvailable, available)
        else:
            reply.rightsAvailable = available
        
    # ----------------------------------------------------------------
    
    def iterAvailableRights(self, serviceRights, method):
        '''
        Iterates the rights that have permissions.
        '''
        for right in serviceRights:
            assert isinstance(right, RightService)
            
            structNode = self.repositoryNodeService.process(right.structure)
            assert isinstance(structNode, StructNode)
            if not structNode.calls: continue
            
            if method is None:
                yield right
                continue
            
            assert isinstance(method, int), 'Invalid method %s' % method
            for structCall in structNode.calls:
                assert isinstance(structCall, StructCall)
                if method & structCall.call.method: yield right

@injected
@setup(Handler, name='iterateResourcePermissions')
class IterateResourcePermissions(HandlerProcessorProceed):
    '''
    Provides the handler that iterates the permissions.
    '''
    
    repositoryNodeService = RepositoryNodeService; wire.entity('repositoryNodeService')
    # The repository node service to use for extracting the node structures.

    def __init__(self):
        assert isinstance(self.repositoryNodeService, RepositoryNodeService), \
        'Invalid repository node service %s' % self.repositoryNodeService
        super().__init__()

    def process(self, Permission:PermissionResource, solicitation:SolicitationWithPermissions, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the permissions.
        '''
        assert issubclass(Permission, PermissionResource), 'Invalid permission class %s' % Permission
        assert isinstance(solicitation, SolicitationWithPermissions), 'Invalid solicitation %s' % solicitation
        assert isinstance(solicitation.rights, Iterable), 'Invalid rights %s' % solicitation.rights
        
        structures, unprocessed = [], []
        for right in solicitation.rights:
            if isinstance(right, RightService):
                assert isinstance(right, RightService)
                structures.append(right.structure)
            else:
                assert isinstance(right, RightAcl), 'Invalid right %s' % right
                unprocessed.append(right)
            
        solicitation.rights = unprocessed
        
        if SolicitationWithPermissions.node in solicitation: nodeId = id(solicitation.node)
        else: nodeId = None
        
        # Process the indexed structure for the structures
        indexed = {}
        for structure in structures:
            structNode = self.repositoryNodeService.process(structure)
            assert isinstance(structNode, StructNode), 'Invalid structure node %s' % structNode
            for structCall, structNodeInvokers in structNode.calls.items():
                assert isinstance(structCall, StructCall)
                assert isinstance(structNodeInvokers, StructNodeInvokers)
                
                # Processing invokers
                indexedServices = indexed.get(structCall.call.method)
                if indexedServices is None: indexedServices = indexed[structCall.call.method] = {}
                
                indexedCalls = indexedServices.get(structCall.serviceType)
                if indexedCalls is None: indexedCalls = indexedServices[structCall.serviceType] = {}
                
                invokersAndFilters = indexedCalls.get(structCall.call.name)
                if invokersAndFilters is None:
                    invokersAndFilters = indexedCalls[structCall.call.name] = ({}, {})
                    isFirst = True
                else: isFirst = False
                indexInvokers, filters = invokersAndFilters
                
                if nodeId:
                    invoker = structNodeInvokers.invokers.get(nodeId)
                    if invoker is None: continue
                    indexInvokers[nodeId] = invoker
                else: indexInvokers.update(structNodeInvokers.invokers)
                
                if Solicitation.method in solicitation:
                    if not solicitation.method & structCall.call.method: continue
                assert isinstance(structCall.call, Call)
                
                # Processing filters
                if structCall.filters:
                    if isFirst: filters.update(structCall.filters)
                    elif filters:  # Means there is something in the filters
                        oldFilters = dict(filters)
                        filters.clear()
                        for resourceType, structFilter in structCall.filters.items():
                            assert isinstance(structFilter, Filter)
                            resourceFilter = oldFilters.get(resourceType)
                            if not resourceFilter: continue
                            assert isinstance(resourceFilter, Filter)
                            
                            if resourceFilter.priority > structFilter.priority: filters[resourceType] = structFilter
                            else: filters[resourceType] = resourceFilter
                elif filters: filters.clear()  # Clear all the filters since this structure requires no filtering
        
        permissions = self.iterPermissions(indexed, Permission)
        
        if SolicitationWithPermissions.permissions in solicitation:
            solicitation.permissions = chain(solicitation.permissions, permissions)
        else:
            solicitation.permissions = permissions
                        
    # ----------------------------------------------------------------
    
    def iterPermissions(self, indexed, Permission):
        '''
        Iterates the permissions for the provided indexed structure.
        '''
        for indexedMethod, indexedServices in indexed.items():
            for indexedCalls in indexedServices.values():
                for indexInvokers, filters in indexedCalls.values():
                    for structInvoker in indexInvokers.values():
                        assert isinstance(structInvoker, StructInvoker)
                        path = pathForNode(structInvoker.node)
                        assert isinstance(path, Path)
                        # We need to check if the returned node has at least one filter in the path.
                        # TODO: check implementation, since this was done in a hurry
#                        available = []
#                        for resourceType, filter in filters.items():
#                            for match in path.matches:
#                                if isinstance(match, MatchProperty):
#                                    assert isinstance(match, MatchProperty)
#                                    assert isinstance(match.node, NodeProperty)
#                                    if resourceType in match.node.typesProperties:
#                                        available.append(filter)
#                                        break
                        yield Permission(method=indexedMethod, path=path, invoker=structInvoker.invoker,
                                         filters=list(filters.values()))

# --------------------------------------------------------------------

class StructNode(Bean):
    '''
    The structure for node.
    '''
    
    calls = dict; calls = Attribute(calls, factory=dict, doc='''
    @rtype: dictionary{StructCall, StructNodeInvokers}
    The structure node invokers indexed by the structure call.
    ''')

class StructNodeInvokers(Bean):
    '''
    The structure for node invokers.
    '''
    
    invokers = dict; invokers = Attribute(invokers, factory=dict, doc='''
    @rtype: dictionary{integer, StructInvoker}
    The invoker structure indexed by the node id.
    ''')       
    
class StructInvoker(Bean):
    '''
    The structure for invoker.
    '''

    invoker = Invoker; invoker = Attribute(invoker, doc='''
    @rtype: Invoker
    The invoker.
    ''')
    node = Node; node = Attribute(node, doc='''
    @rtype: Node
    The invoker node.
    ''')
