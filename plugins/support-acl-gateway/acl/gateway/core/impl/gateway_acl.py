'''
Created on Jan 21, 2013

@package: security acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL access service.
'''

from ..spec import IGatewayAclService, IAuthenticatedProvider
from acl.gateway.api.filter import IAclFilter
from acl.spec import RightBase, Filter
from ally.api.config import GET, DELETE, INSERT, UPDATE
from ally.api.operator.container import Model
from ally.api.operator.type import TypeService, TypeProperty
from ally.api.type import typeFor
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Node, ConverterPath, Path, \
    INodeChildListener, INodeInvokerListener, Invoker
from ally.http.spec.server import HTTP_GET, HTTP_DELETE, HTTP_POST, HTTP_PUT
from ally.support.core.util_resources import findNodesFor, pathForNode, \
    propertyTypesOf, ReplacerWithMarkers
from collections import Iterable
from gateway.http.api.gateway import Gateway
import logging
from collections import deque

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@injected
@setup(IGatewayAclService, name='gatewayAclService')
class GatewayAclService(IGatewayAclService, INodeChildListener, INodeInvokerListener):
    '''
    Implementation for @see: IGatewayAclService
    '''
    
    resourcesRoot = Node; wire.entity('resourcesRoot')
    # The root node to process the security rights repository against.
    converterPath = ConverterPath; wire.entity('converterPath')
    # The converter path to be used.
    
    def __init__(self):
        '''
        Construct the access service.
        '''
        assert isinstance(self.resourcesRoot, Node), 'Invalid root node %s' % self.resourcesRoot
        assert isinstance(self.converterPath, ConverterPath), 'Invalid converter path %s' % self.converterPath
        
        self._cacheFilters = {}
        self.resourcesRoot.addStructureListener(self)
        
    def gatewaysFor(self, rights, provider):
        '''
        @see: IGatewayAclService.gatewaysFor
        '''
        if isinstance(rights, RightBase): rights = (rights,)
        assert isinstance(rights, Iterable), 'Invalid rights %s' % rights
        if not isinstance(rights, (list, tuple, deque)): rights = list(rights)
        assert isinstance(provider, IAuthenticatedProvider), 'Invalid authenticated provider %s' % provider
        
        replacer = ReplacerWithMarkers()
        
        gateways, gatewaysGETByPattern = [], {}
        # Process GET gateways
        for _method, path, invoker, filters in RightBase.iterPermissions(self.resourcesRoot, rights, GET):
            assert isinstance(path, Path), 'Invalid path %s' % path
            
            gateway = Gateway()
            gateway.Methods = [HTTP_GET]
            gateway.Pattern, types = self.processPattern(path, invoker, replacer)
            gateway.Filters = self.processFilters(types, filters, provider, replacer)
            
            gatewaysGETByPattern[gateway.Pattern] = gateway
            gateways.append(gateway)
        
#        # Process DELETE access
#        for _method, path, invoker, filters in RightBase.iterPermissions(self.resourcesRoot, rights, DELETE):
#            assert isinstance(path, Path)
#            
#            filtersWithPath = self._processFilters(filters, replacer)
#            data = self._processPatternWithFilters(path, invoker, filtersWithPath, replacer)
#            
#            pattern, accessFilters, accessMarkers = data
#            
#            access = accessesGetByPattern.get(pattern)
#            if access and access.Filter == accessFilters:
#                access.Methods.append(HTTP_DELETE)
#                continue
#            
#            access = AclAccess()
#            access.Methods = [HTTP_DELETE, HTTP_GET]  # Needed to add get also because of the method overide
#            access.Pattern = pattern
#            access.Filter = accessFilters
#            if accessMarkers: access.markers.update(accessMarkers)
#            
#            accesses.append(access)
#        
#        # TODO: properly implement the secured redirect
#        accessesUpdateByPattern = {}
#        # Process POST access
#        for _method, path, invoker, filters in RightBase.iterPermissions(self.resourcesRoot, rights, INSERT):
#            assert isinstance(path, Path)
#            
#            access = AclAccess()
#            access.Methods = [HTTP_POST]
#            access.Pattern = self._processPatternWithSecured(path, invoker, replacer)
#            
#            accessesUpdateByPattern[access.Pattern] = access
#            accesses.append(access)
#            
#        # Process PUT access
#        for _method, path, invoker, filters in RightBase.iterPermissions(self.resourcesRoot, rights, UPDATE):
#            assert isinstance(path, Path)
#            
#            pattern = self._processPatternWithSecured(path, invoker, replacer)
#            
#            access = accessesUpdateByPattern.get(pattern)
#            if access:
#                access.Methods.append(HTTP_PUT)
#                continue
#            
#            access = AclAccess()
#            access.Methods = [HTTP_PUT, HTTP_POST]  # Needed to add post also because of the method overide
#            access.Pattern = pattern
#            
#            accesses.append(access)
        
        gateways.sort(key=lambda gateway: (gateway.Pattern, gateway.Methods))
        return gateways
    
    # ----------------------------------------------------------------
    
    def onChildAdded(self, node, child):
        '''
        @see: INodeChildListener.onChildAdded
        '''
        self._cacheFilters.clear()
    
    def onInvokerChange(self, node, old, new):
        '''
        @see: INodeInvokerListener.onInvokerChange
        '''
        self._cacheFilters.clear()
        
    # ----------------------------------------------------------------
    
    def processPattern(self, path, invoker, replacer):
        '''
        Process the gateway pattern creating groups for all property types present in the path.
        
        @param path: Path
            The path to process as a gateway pattern.
        @param invoker: Invoker
            The invoker to process the pattern based on.
        @param replacer: ReplacerWithMarkers
            The replacer to use for marking the pattern with groups.
        @return: tuple(string, list[TypeProperty])
            Returns the gateway pattern and the property types that the pattern has capturing groups for.
        '''
        assert isinstance(path, Path), 'Invalid path %s' % path
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(replacer, ReplacerWithMarkers), 'Invalid replacer %s' % replacer
        
        replaceMarkers, types = [], []
        for propertyType in propertyTypesOf(path, invoker):
            assert isinstance(propertyType, TypeProperty), 'Invalid property type %s' % propertyType
            
            if propertyType.isOf(int): replaceMarkers.append('([0-9\\-]+)')
            elif propertyType.isOf(str): replaceMarkers.append('([^\\/]+)')
            else: raise Exception('Unusable type \'%s\'' % propertyType)
            types.append(propertyType)
        
        replacer.register(replaceMarkers)
        return ''.join(('\\/'.join(path.toPaths(self.converterPath, replacer)), '[\\/]?(?:\\.|$)')), types
    
    def processFilters(self, types, filters, provider, replacer):
        '''
        Process the filters into path filters.
        
        @param types: list[TypeProperty]
            The type properties that have groups in the gateway pattern, they must be in the proper order that they are
            captured.
        @param filters: Iterable(Filter)
            The filters to process.
        @param provider: IAuthenticatedProvider
            The @see: IAuthenticatedProvider used in solving the filters paths.
        @param replacer: ReplacerWithMarkers
            The replacer to use on the path.
        @return: dictionary{TypeProperty, tuple(string, dictionary{TypeProperty: string}}
            A dictionary containing {resource type, (marked path, {authenticated type: marker}}
        '''
        assert isinstance(types, list), 'Invalid types %s' % types
        assert isinstance(filters, Iterable), 'Invalid filters %s' % filter
        assert isinstance(replacer, ReplacerWithMarkers), 'Invalid replacer %s' % replacer
        
        paths = None
        for rfilter in filters:
            assert isinstance(rfilter, Filter), 'Invalid filter %s' % rfilter
            
            try: index = types.index(rfilter.resource)
            except ValueError:
                log.error('Invalid gateway pattern type %s', rfilter.resource)
                continue
            
            path = self.processFilter(rfilter, provider, '{%s}' % (index + 1), replacer)
            if path is not None:
                if paths is None: paths = [path]
                else: paths.append(path)
                
        return paths
    
    def processFilter(self, rfilter, provider, marker, replacer):
        '''
        Process the provided filter.
        
        @param rfilter: Filter
            The resource filter to process.
        @param provider: IAuthenticatedProvider
            The @see: IAuthenticatedProvider used in solving the filters paths.
        @param marker: string
            The resource marker to place in the filter path, this marker is used to identify the group in the gateway pattern.
        @param replacer: ReplacerWithMarkers
            The replacer to use on the filter path.
        @return: string|None
            The marked filter path, None if the filter is invalid.
        '''
        assert isinstance(rfilter, Filter), 'Invalid filter %s' % rfilter
        assert isinstance(rfilter.filter, IAclFilter), 'Invalid filter %s of %s' % (rfilter.filter, rfilter)
        typeService = typeFor(rfilter.filter)
        assert isinstance(typeService, TypeService), 'Invalid filter %s, is not a REST service' % rfilter.filter
        assert isinstance(provider, IAuthenticatedProvider), 'Invalid authenticated provider %s' % provider
        assert isinstance(marker, str), 'Invalid marker %s' % marker
        assert isinstance(replacer, ReplacerWithMarkers), 'Invalid replacer %s' % replacer
        
        path = self._cacheFilters.get(typeService)
        if not path:
            nodes = findNodesFor(self.resourcesRoot, typeService, 'isAllowed')
            if not nodes:
                log.error('The filter service %s cannot be located in the resources tree', typeService)
                return
            if len(nodes) > 1:
                log.error('To many nodes for service %s in the resources tree, don\'t know which one to use', typeService)
                return
            
            node = nodes[0]
            assert isinstance(node, Node)
            path = pathForNode(node)
            
            if __debug__:
                # Just checking that the properties are ok
                propertyTypes = propertyTypesOf(path, node.get)
                assert len(propertyTypes) == 2, 'Invalid path %s for filter' % path
                indexAuth = propertyTypes.index(rfilter.authenticated)
                assert indexAuth >= 0, 'Invalid authenticated %s for path %s' % (rfilter.authenticated, path)
                indexRsc = propertyTypes.index(rfilter.resource)
                assert indexRsc >= 0, 'Invalid resource %s for path %s' % (rfilter.resource, path)
                assert indexAuth < indexRsc, 'Invalid path %s, improper order for types' % path
    
        assert isinstance(path, Path), 'Invalid path %s' % path
        valueAuth = provider.valueFor(rfilter.authenticated)
        if valueAuth is None:
            log.error('The filter service %s has not authenticated value for %s', typeService, rfilter.authenticated)
            return
        
        replacer.register((valueAuth, marker))
        return '/'.join(path.toPaths(self.converterPath, replacer))
    
