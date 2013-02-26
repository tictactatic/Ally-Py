'''
Created on Feb 26, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processors that creates Gateway objects specific for persistence, also provides support for handling the persistence filtering
on server side.
'''

from acl.spec import Filter
from ally.api.operator.container import Model
from ally.api.operator.type import TypeProperty, TypeModel, TypeModelProperty
from ally.api.type import Input
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Node, Invoker, INodeInvokerListener, Path
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import Handler, HandlerBranchingProceed
from ally.design.processor.processor import Included, Using
from ally.http.spec.server import IEncoderHeader, IDecoderHeader
from ally.support.core.util_resources import propertyTypesOf
from collections import Iterable, Callable
from gateway.api.gateway import Gateway
from itertools import chain
import logging
import weakref
from ally.api.config import UPDATE, INSERT

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@injected
@setup(name='persistenceFilterService')
class PersistenceFilterService(INodeInvokerListener):
    '''
    The service used for getting the persistence filters for invokers.
    '''
    
    def __init__(self):
        '''
        Construct the persistence invoker service.
        '''
        self._cacheTypes = {}
        
    def onInvokerChange(self, node, old, new):
        '''
        @see: INodeInvokerListener.onInvokerChange
        '''
        self._cacheTypes.pop(id(node), None)
        
    # ----------------------------------------------------------------
        
    def extractModelFilter(self, node, invoker, filters):
        '''
        Extracts the model filters based on the invoker and filters, the node is mostly used to check if there is no ambiguity
        for filters.

        @param node: Node
            The node where the invoker is placed.
        @param invoker: Invoker
            The invoker to check.
        @param filters: list[Filter]
            The filters to be trimmed.
        @return: list[Filter]|None
            The model filters or None if there no such filters.
        '''
        assert isinstance(node, Node), 'Invalid node %s' % node
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(filters, list), 'Invalid filters %s' % filters
        
        types = self.typesFor(node, invoker)
        # If there are no property types then no trimming is required
        if not types: return
        typesModel, typesPath = types
        
        modelFilters = []
        for rfilter in filters:
            assert isinstance(rfilter, Filter), 'Invalid filter %s' % rfilter
            assert isinstance(rfilter.resource, TypeModelProperty), 'Invalid resource property %s' % rfilter.resource
            assert isinstance(rfilter.resource.container, Model), 'Invalid model %s' % rfilter.resource.container
            occModel = typesModel.count(rfilter.resource)
            if occModel == 0: continue  # If the property is not in the model we continue
            if occModel > 1:
                log.error('Ambiguous resource filter type \'%s\', has to many occurrences in model types: %s',
                          rfilter.resource, ', '.join(str(typ) for typ in typesModel))
                continue
            occPath = typesPath.count(rfilter.resource)
            if occPath > 0:
                # If the invoker is UPDATE then based on @see: AssembleUpdateModel we have a possible duplication
                if invoker.method != UPDATE:
                    log.error('Ambiguous resource filter type \'%s\', has to many occurrences in path types: %s '
                              'and model types: %s', rfilter.resource, ', '.join(str(typ) for typ in typesPath),
                              ', '.join(str(typ) for typ in typesModel))
                continue
            # TODO: uncomment
#            if invoker.method == INSERT and rfilter.resource.container.propertyId == rfilter.resource.property:
#                # If the filtered resource is the property id and we are in INSERT has no sense for filtering.
#                continue
            
            modelFilters.append(rfilter)
            
        return modelFilters if modelFilters else None
        
    # ----------------------------------------------------------------
    
    def typesFor(self, node, invoker):
        '''
        Provides the merged types for the path inputs and model inputs.
        
        @param node: Node
            The node where the invoker is placed.
        @param invoker: Invoker
            The invoker to provide the types.
        @return: tuple(list[TypeProperty], list[TypeProperty])|None
            The list of property types, on the first position the models property types and on the second position the
            path property types for the invoker, None if the invoker has no model inputs.
        '''
        assert isinstance(node, Node), 'Invalid node %s' % node
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        
        nodeId = id(node)
        cache = self._cacheTypes.get(nodeId)
        if cache is None:
            cache = self._cacheTypes[nodeId] = {}
            node.addNodeListener(self)
        else:
            item = cache.get(invoker)
            if item is not None:
                ref, value = item
                if ref() != None: return value
            
        propertyTypes = []
        # First we find out if there are any model inputs.
        for inp in invoker.inputs:
            assert isinstance(inp, Input), 'Invalid input %s' % inp
            if isinstance(inp.type, TypeModel):
                assert isinstance(inp.type, TypeModel)
                propertyTypes.extend(inp.type.childTypes())
        
        # If there are no model property types then no trimming is required
        if not propertyTypes: value = None
        else: value = (propertyTypes, propertyTypesOf(node, invoker))
        cache[invoker] = (weakref.ref(node), value)

        return value

# --------------------------------------------------------------------

class HeaderConfigurations:
    '''
    Provides the common header configurations to be used for persist filtering.
    '''
    
    nameHeader = 'X-Authenticated'
    # The header name used for placing the authenticated data into.
    separatorHeader = ':'
    # The separator used between the header name and header value. 
    
    def __init__(self):
        assert isinstance(self.nameHeader, str), 'Invalid header name %s' % self.nameHeader
        assert isinstance(self.separatorHeader, str), 'Invalid header separator %s' % self.separatorHeader
    
    # ----------------------------------------------------------------
    
    def nameFor(self, typeProperty):
        '''
        Provides the name for the property type.
        
        @param typeProperty: TypeProperty
            The property type to generate a name for.
        @return: string
            The name of the property type.
        '''
        assert isinstance(typeProperty, TypeProperty), 'Invalid property type %s' % typeProperty
        assert isinstance(typeProperty.container, Model), 'Invalid model %s' % typeProperty.container
        return '%s.%s' % (typeProperty.container.name, typeProperty.property)

# --------------------------------------------------------------------

class PermissionResource(Context):
    '''
    The permission context.
    '''
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
    provider = requires(Callable)

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    gateways = defines(Iterable, doc='''
    @rtype: Iterable(Gateway)
    The resource permissions generated gateways.
    ''')

class RequestEncode(Context):
    '''
    The request encode headers context.
    '''
    # ---------------------------------------------------------------- Defined
    headers = requires(dict)
    encoderHeader = requires(IEncoderHeader)

class SolicitationGateways(Context):
    '''
    The persistence gateways reply context.
    '''
    # ---------------------------------------------------------------- Defined
    permissions = defines(Iterable)
    provider = defines(Callable)
    
class ReplyGateways(Context):
    '''
    The persistence gateways reply context.
    '''
    # ---------------------------------------------------------------- Required
    gateways = requires(Iterable)
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='gatewaysPersistenceFromPermissions')
class GatewaysPersistenceFromPermissions(HandlerBranchingProceed, HeaderConfigurations):
    '''
    Processor that provides the gateways that will require persistence filtering on the server side.
    '''
    
    persistenceFilterService = PersistenceFilterService; wire.entity('persistenceFilterService')
    # The persistence filter service.
    assemblyPersistenceGateways = Assembly; wire.entity('assemblyPersistenceGateways')
    # The assembly used for creating the gateways specific for persistence.
    
    def __init__(self):
        assert isinstance(self.persistenceFilterService, PersistenceFilterService), \
        'Invalid persistence service %s' % self.persistenceFilterService
        assert isinstance(self.assemblyPersistenceGateways, Assembly), 'Invalid assembly %s' % self.assemblyPersistenceGateways
        HandlerBranchingProceed.__init__(self, Included(self.assemblyPersistenceGateways).
                                         using(solicitation=SolicitationGateways, reply=ReplyGateways))
        HeaderConfigurations.__init__(self)

    def process(self, processing, Permission:PermissionResource, solicitation:Solicitation, reply:Reply,
                request:RequestEncode, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Construct the persistence gateways for permissions.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert issubclass(Permission, PermissionResource), 'Invalid permission class %s' % Permission
        assert isinstance(solicitation, Solicitation), 'Invalid solicitation %s' % solicitation
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        assert isinstance(request, RequestEncode), 'Invalid request %s' % request
        assert isinstance(solicitation.permissions, Iterable), 'Invalid permissions %s' % solicitation.permissions
        assert callable(solicitation.provider), 'Invalid provider %s' % solicitation.provider
        assert isinstance(request.encoderHeader, IEncoderHeader), 'Invalid header encoder %s' % request.encoderHeader
        
        authenticatedTypes, authenticated, unprocessed = set(), [], []
        for permission in solicitation.permissions:
            assert isinstance(permission, PermissionResource), 'Invalid permission %s' % permission
            assert isinstance(permission.path, Path), 'Invalid path %s' % permission.path
            filters = self.persistenceFilterService.extractModelFilter(permission.path.node, permission.invoker,
                                                                       permission.filters)
            if not filters:
                unprocessed.append(permission)
                continue
            
            authenticated.append(permission)
            for rfilter in filters:
                assert isinstance(rfilter, Filter), 'Invalid filter %s' % rfilter
                authenticatedTypes.add(rfilter.authenticated)
                # We need to adjust the permission filters.
                permission.filters.remove(rfilter)
        
        values = []
        for typeProperty in authenticatedTypes:
            valueAuth = solicitation.provider(typeProperty)
            if valueAuth is None:
                log.error('No authenticated value for %s', rfilter.authenticated)
                continue
            assert isinstance(valueAuth, str), 'Invalid value %s for %s' % (valueAuth, typeProperty)
            values.append((valueAuth, ('property', self.nameFor(typeProperty))))
            
        if values:
            request.encoderHeader.encode(self.nameHeader, *values)
            headers = [self.separatorHeader.join(nameValue) for nameValue in request.headers.items()]
            
            solGateways = processing.ctx.solicitation()
            assert isinstance(solGateways, SolicitationGateways)
            
            solGateways.permissions = authenticated
            solGateways.provider = solicitation.provider
            
            chainGateways = Chain(processing)
            chainGateways.process(Permission=Permission, solicitation=solGateways,
                                  reply=processing.ctx.reply(), **keyargs).doAll()
        
            replyGateways = chainGateways.arg.reply
            assert isinstance(replyGateways, ReplyGateways), 'Invalid reply %s' % replyGateways
            assert isinstance(replyGateways.gateways, Iterable), 'Invalid reply gateways %s' % replyGateways.gateways
            
            gateways = list(replyGateways.gateways)
            for gateway in gateways:
                assert isinstance(gateway, Gateway), 'Invalid gateway %s' % gateway
                if Gateway.PutHeaders not in gateway: gateway.PutHeaders = list(headers)
                else: gateway.PutHeaders.extend(headers)
            
            if Reply.gateways in reply:
                reply.gateways = chain(reply.gateways, gateways)
            else:
                reply.gateways = gateways
        else:
            unprocessed = chain(authenticated, unprocessed)
            
        solicitation.permissions = unprocessed

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    decoderHeader = requires(IDecoderHeader)
    path = requires(Path)
    invoker = requires(Invoker)
    arguments = requires(dict)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(str)
    status = defines(int)
    isSuccess = defines(bool)
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='filterInvoking')
class FilterInvoking(HandlerBranchingProceed, HeaderConfigurations):
    '''
    Processor that provides the model filtering.
    '''
    
    persistenceFilterService = PersistenceFilterService; wire.entity('persistenceFilterService')
    # The persistence filter service.
    assemblyFilterPermissions = Assembly; wire.entity('assemblyFilterPermissions')
    # The assembly used for getting the filter permissions.
    
    def __init__(self):
        assert isinstance(self.persistenceFilterService, PersistenceFilterService), \
        'Invalid persistence service %s' % self.persistenceFilterService
        assert isinstance(self.assemblyFilterPermissions, Assembly), 'Invalid assembly %s' % self.assemblyFilterPermissions
        HandlerBranchingProceed.__init__(self, Using(self.assemblyFilterPermissions, ))
        HeaderConfigurations.__init__(self)

    def process(self, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Filter the invoking if is the case.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error
        
        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid header decoder %s' % request.decoderHeader
        authenticated = request.decoderHeader.decode(self.nameHeader)
        if not authenticated: return  # Skip if no authenticated header is provided
        
        assert isinstance(request.path, Path), 'Invalid path %s' % request.path
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        
        
        
