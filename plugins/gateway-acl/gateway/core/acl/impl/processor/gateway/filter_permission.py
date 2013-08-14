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
    filtersPaths = defines(dict, doc='''
    @rtype: dictionary{string: set(string)}
    The filters paths for this permission indexed by the target path marker.
    ''')
    # ---------------------------------------------------------------- Optional
    nodesValues = optional(dict)
    # ---------------------------------------------------------------- Required
    pathMarkers = requires(dict)
    filters = requires(dict)

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
        super().__init__(Permission=Permission, Invoker=Invoker, Element=Element, ACLFilter=ACLFilter)
    
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
        assert rootURI is None or isinstance(rootURI, list), 'Invalid root URI %s' % rootURI
        
        for permission in permissions:
            assert isinstance(permission, Permission), 'Invalid permission %s' % permission
            
            if permission.filters:
                assert isinstance(permission.filters, dict), 'Invalid filters %s' % permission.filters
                
                if permission.filtersPaths is None: permission.filtersPaths = {}
                for aclFilter, nodes in permission.filters.items():
                    assert isinstance(aclFilter, ACLFilter), 'Invalid filter %s' % aclFilter
                    assert isinstance(aclFilter.targets, set), 'Invalid targets %s' % aclFilter.targets
                    assert isinstance(permission.pathMarkers, dict), 'Invalid path makers %s' % permission.pathMarkers
                    
                    for node in nodes:
                        assert node in permission.pathMarkers, 'No marker available for %s' % node
                        pathMarker = permission.pathMarkers[node]
                        assert isinstance(pathMarker, str), 'Invalid marker %s for %s' % (pathMarker, node)
                        
                        for invoker in aclFilter.invokers:
                            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
                            
                            items = []
                            if rootURI: items.extend(rootURI)
                            for el in invoker.path:
                                assert isinstance(el, Element), 'Invalid element %s' % el
                                if el.name: items.append(el.name)
                                elif el.node in aclFilter.targets: items.append(pathMarker)
                                else:
                                    assert Permission.nodesValues in permission, 'No value available for %s' % el.node
                                    assert el.node in permission.nodesValues, 'No value available for %s' % el.node
                                    assert isinstance(permission.nodesValues[el.node], str), \
                                    'Invalid value %s for %s' % (permission.nodesValues[el.node], el.node)
                                    items.append(permission.nodesValues[el.node])
                            paths = permission.filtersPaths.get(pathMarker)
                            if paths is None: paths = permission.filtersPaths[pathMarker] = set()
                            paths.add('/'.join(items))
                        
            yield permission
