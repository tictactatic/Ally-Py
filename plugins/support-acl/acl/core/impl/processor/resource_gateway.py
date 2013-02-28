'''
Created on Feb 21, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that creates Gateway objects based on resource permissions.
'''

from acl.api.filter import IAclFilter
from acl.spec import Filter
from ally.api.config import GET, DELETE, INSERT, UPDATE
from ally.api.operator.type import TypeService, TypeProperty
from ally.api.type import typeFor
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Node, ConverterPath, Path, \
    INodeChildListener, INodeInvokerListener, Invoker
from ally.design.processor.attribute import defines, requires, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed, Handler
from ally.http.spec.server import HTTP_GET, HTTP_DELETE, HTTP_POST, HTTP_PUT
from ally.support.core.util_resources import findNodesFor, propertyTypesOf, \
    ReplacerWithMarkers, pathForNode
from collections import Callable, Iterable
from gateway.api.gateway import Gateway
from itertools import chain
import logging
import re

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

TO_HTTP_METHOD = {GET: HTTP_GET, DELETE: HTTP_DELETE, INSERT: HTTP_POST, UPDATE: HTTP_PUT}
# The mapping from configuration methods to http methods.

# --------------------------------------------------------------------

class PermissionResource(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Optional
    values = optional(dict)
    # ---------------------------------------------------------------- Required
    method = requires(int)
    path = requires(Path)
    invoker = requires(Invoker)
    filters = requires(list)
    
class Solicitation(Context):
    '''
    The solicitation context.
    '''
    # ---------------------------------------------------------------- Required
    permissions = requires(Iterable)
    provider = requires(Callable, doc='''
    @rtype: callable(TypeProperty) -> string|None
    Callable used for getting the authenticated value for the provided property type.
    ''')

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    gateways = defines(Iterable, doc='''
    @rtype: Iterable(Gateway)
    The resource permissions generated gateways.
    ''')

# --------------------------------------------------------------------

@injected
@setup(Handler, name='gatewaysFromPermissions')
class GatewaysFromPermissions(HandlerProcessorProceed, INodeChildListener, INodeInvokerListener):
    '''
    Provides the handler that creates gateways based on resource permissions.
    '''
    
    resourcesRoot = Node; wire.entity('resourcesRoot')
    # The root node to find the filters in.
    converterPath = ConverterPath; wire.entity('converterPath')
    # The converter path to be used.
    
    root_uri_resources = str; wire.config('root_uri_resources', doc='''
    This will be used for adjusting the gateways patterns and filters with a root URI. It needs to have the place holder '%s',
    something like 'resources/%s'.
    ''')

    def __init__(self):
        assert isinstance(self.resourcesRoot, Node), 'Invalid root node %s' % self.resourcesRoot
        assert isinstance(self.converterPath, ConverterPath), 'Invalid converter path %s' % self.converterPath
        assert isinstance(self.root_uri_resources, str), 'Invalid root resources uri %s' % self.root_uri_resources
        super().__init__()
        
        parts = self.root_uri_resources.split('%s')
        parts = (re.escape(part) for part in parts)
        self.rootPatternResources = '%s'.join(parts)
        self._cacheFilters = {}
        self.resourcesRoot.addStructureListener(self)

    def process(self, Permission:PermissionResource, solicitation:Solicitation, reply:Reply, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Construct the gateways for permissions.
        '''
        assert issubclass(Permission, PermissionResource), 'Invalid permission class %s' % Permission
        assert isinstance(solicitation, Solicitation), 'Invalid solicitation %s' % solicitation
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        assert isinstance(solicitation.permissions, Iterable), 'Invalid permissions %s' % solicitation.permissions
        assert callable(solicitation.provider), 'Invalid provider %s' % solicitation.provider
        
        gateways = self.processGateways(solicitation.permissions, solicitation.provider)
        if Reply.gateways in reply:
            reply.gateways = chain(reply.gateways, gateways)
        else:
            reply.gateways = gateways
    
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
    
    def processGateways(self, permissions, provider):
        '''
        Process the gateways for the provided permissions.
        
        @param permissions: Iterable(PermissionResource)
            The permissions to create the gateways for.
        @param provider: callable
            The callable used in solving the authenticated values.
        @return: list[Gateway]
            The created gateways objects.
        '''
        assert isinstance(permissions, Iterable), 'Invalid permissions %s' % permissions
        
        replacer, gateways, gatewaysByPattern = ReplacerWithMarkers(), [], {}
        for permission in permissions:
            assert isinstance(permission, PermissionResource), 'Invalid permission resource %s' % permission
            
            pattern, types = self.processPattern(permission.path, permission.invoker, replacer, permission.values)
            filters = self.processFilters(types, permission.filters, provider, replacer)
            
            gateway = gatewaysByPattern.get(pattern)
            if gateway and gateway.Filters == filters:
                gateway.Methods.append(TO_HTTP_METHOD[permission.method])
            else:
                gateway = Gateway()
                gateway.Methods = [TO_HTTP_METHOD[permission.method]]
                gateway.Pattern = self.rootPatternResources % pattern
                gateway.Filters = filters
                
                gatewaysByPattern[pattern] = gateway
                gateways.append(gateway)
        return gateways
    
    def processPattern(self, path, invoker, replacer, values=None):
        '''
        Process the gateway pattern creating groups for all property types present in the path.
        
        @param path: Path
            The path to process as a gateway pattern.
        @param invoker: Invoker
            The invoker to process the pattern based on.
        @param replacer: ReplacerWithMarkers
            The replacer to use for marking the pattern with groups.
        @param values: dictionary{TypeProperty: string}
            The static values to be placed on the path, as a key the type property that has the value.
        @return: tuple(string, list[TypeProperty])
            Returns the gateway pattern and the property types that the pattern has capturing groups for.
        '''
        assert isinstance(path, Path), 'Invalid path %s' % path
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(replacer, ReplacerWithMarkers), 'Invalid replacer %s' % replacer
        
        replaceMarkers, types = [], []
        for propertyType in propertyTypesOf(path, invoker):
            assert isinstance(propertyType, TypeProperty), 'Invalid property type %s' % propertyType
            
            if values:
                assert isinstance(values, dict), 'Invalid values %s' % values
                value = values.get(propertyType)
                if value is not None:
                    assert isinstance(value, str), 'Invalid value %s' % value
                    replaceMarkers.append(re.escape(value))
                    continue
                
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
        @param provider: callable
            The callable used in solving the authenticated values.
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
            occurence = types.count(rfilter.resource)
            if occurence > 1:
                log.error('Ambiguous resource filter type \'%s\', has to many occurrences in path types: %s', rfilter.resource,
                          ','.join(str(typ) for typ in types) if types else 'no types')
                continue
            elif occurence == 0:
                assert log.debug('Invalid resource filter type \'%s\', is not present in the path types: %s', rfilter.resource,
                                 ','.join(str(typ) for typ in types) if types else 'no types') or True
                continue
            
            path = self.processFilter(rfilter, provider, '{%s}' % (types.index(rfilter.resource) + 1), replacer)
            if path is not None:
                if paths is None: paths = [self.root_uri_resources % path]
                else: paths.append(self.root_uri_resources % path)
                
        return paths
    
    def processFilter(self, rfilter, provider, marker, replacer):
        '''
        Process the provided filter.
        
        @param rfilter: Filter
            The resource filter to process.
        @param provider: callable
            The callable used in solving the authenticated values.
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
        assert callable(provider), 'Invalid authenticated provider %s' % provider
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
        valueAuth = provider(rfilter.authenticated)
        if valueAuth is None:
            log.error('The filter service %s has not authenticated value for %s', typeService, rfilter.authenticated)
            return
        
        replacer.register((valueAuth, marker))
        return '/'.join(path.toPaths(self.converterPath, replacer))
