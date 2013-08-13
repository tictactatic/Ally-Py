'''
Created on Aug 13, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that handles the permissions filters.
'''

from ally.container.support import setup
from ally.design.processor.attribute import defines, requires, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from collections import Iterable

# --------------------------------------------------------------------

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Optional
    rootURI = optional(list)
    # ---------------------------------------------------------------- Required
    permissions = requires(Iterable)

class Permission(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Defined
    filtersPath = defines(dict, doc='''
    @rtype: dictionary{string: set(string)}
    The filters paths for this permission indexed by the target node marker.
    ''')
    # ---------------------------------------------------------------- Optional
    nodesValues = optional(dict)
    # ---------------------------------------------------------------- Required
    methodACL = requires(Context)
    groups = requires(set)
    nodesMarkers = requires(dict)

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(list)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Context)
    name = requires(str)
    
class ACLMethod(Context):
    '''
    The ACL method context.
    '''
    # ---------------------------------------------------------------- Required
    filters = requires(dict)

class ACLFilter(Context):
    '''
    The ACL filter context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    targets = requires(set)
     
# --------------------------------------------------------------------

@setup(Handler, name='filterPermission')
class FilterPermission(HandlerProcessor):
    '''
    Provides the handler that handles the permissions filters.
    '''
    
    def __init__(self):
        super().__init__(Permission=Permission, Invoker=Invoker, Element=Element, ACLMethod=ACLMethod, ACLFilter=ACLFilter)
    
    def process(self, chain, reply:Reply, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the permissions filters.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        if reply.permissions is None: return
        
        if Reply.rootURI in reply: rootURI = reply.rootURI
        else: rootURI = None
        reply.permissions = self.filterPermissions(reply.permissions, rootURI)

    # ----------------------------------------------------------------
    
    def filterPermissions(self, permissions, rootURI=None):
        '''
        Adds the filters for permissions.
        '''
        assert isinstance(permissions, Iterable), 'Invalid permissions %s' % permissions
        
        for permission in permissions:
            assert isinstance(permission, Permission), 'Invalid permission %s' % permission
            assert isinstance(permission.methodACL, ACLMethod), 'Invalid ACL method %s' % permission.methodACL
            
            if permission.methodACL.filters:
                assert isinstance(permission.methodACL.filters, dict), 'Invalid filters %s' % permission.methodACL.filters
                assert isinstance(permission.groups, set), 'Invalid groups %s' % permission.groups
                for group in permission.groups:
                    filters = permission.methodACL.filters.get(group)
                    if filters: self.pushFilters(permission, filters, rootURI)
                        
            yield permission
            
    def pushFilters(self, permission, filters, rootURI=None):
        '''
        Pushes the filters into permission.
        '''
        assert isinstance(permission, Permission), 'Invalid permission %s' % permission
        assert isinstance(filters, dict), 'Invalid filters %s' % filters
        assert rootURI is None or isinstance(rootURI, list), 'Invalid root URI %s' % rootURI
        
        if permission.filtersPath is None: permission.filtersPath = {}
        for aclFilter, node in filters.values():
            assert isinstance(aclFilter, ACLFilter), 'Invalid filter %s' % aclFilter
            assert isinstance(aclFilter.targets, set), 'Invalid targets %s' % aclFilter.targets
            assert isinstance(permission.nodesMarkers, dict), 'Invalid nodes makers %s' % permission.nodesMarkers
            assert node in permission.nodesMarkers, 'No marker available for %s' % node
            
            nodeMarker = permission.nodesMarkers[node]
            assert isinstance(nodeMarker, str), 'Invalid marker %s for %s' % (nodeMarker, node)
            
            for invoker in aclFilter.invokers:
                assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
                
                items = []
                if rootURI: items.extend(rootURI)
                for el in invoker.path:
                    assert isinstance(el, Element), 'Invalid element %s' % el
                    if el.name: items.append(el.name)
                    elif el.node in aclFilter.targets: items.append(nodeMarker)
                    else:
                        assert Permission.nodesValues in permission, 'No value available for %s' % el.node
                        assert el.node in permission.nodesValues, 'No value available for %s' % el.node
                        assert isinstance(permission.nodesValues[el.node], str), \
                        'Invalid value %s for %s' % (permission.nodesValues[el.node], el.node)
                        items.append(permission.nodesValues[el.node])
                paths = permission.filtersPath.get(nodeMarker)
                if paths is None: paths = permission.filtersPath[nodeMarker] = set()
                paths.add('/'.join(items))
