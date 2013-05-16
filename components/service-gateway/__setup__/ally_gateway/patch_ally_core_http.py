'''
Created on Feb 8, 2013

@package: service gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server patch configuration when used internally with REST.
'''

from ..ally_http.server import assemblyServer
from .processor import GATEWAY_INTERNAL, assemblyRESTRequest, assemblyForward
from .server import server_provide_gateway, gatewayRouter
from ally.container import ioc
from ally.container.error import SetupError
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.http.impl.processor.router_by_path import RoutingByPathHandler
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@ioc.config
def root_uri_my_resources():
    '''
    This will be used for adjusting the encoded URIs to have a root URI whenever used with a gateway internally.
    !Attention this configuration needs to be in concordance with 'server_pattern_gateway' configuration whenever the gateway 
    is used internally.
    '''
    return 'resources/my/%s'

# --------------------------------------------------------------------

try: from .. import ally_core_http
except ImportError:
    log.info('No REST core available, you need to configure an external request assembly for gateway')
    
    @ioc.before(assemblyRESTRequest, assemblyForward)
    def updateAssemblyForResources():
        if server_provide_gateway() == GATEWAY_INTERNAL:
            raise SetupError('Cannot configure internal gateway because the ally core http component is not present')
    
else: 
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------

    from ..ally_core_http.server import resourcesRouter, server_provide_resources, updateAssemblyServerForResources, \
    errorsRouter, server_provide_errors, server_pattern_resources
    from ..ally_core_http.processor import assemblyResources, encoderPathResource, converterPath
    from ally.core.http.impl.processor.path_encoder_resource import ResourcePathEncoderHandler
    
    @ioc.entity
    def encoderPathResourceGateway() -> Handler:
        b = ResourcePathEncoderHandler()
        b.resourcesRootURI = root_uri_my_resources()
        b.converterPath = converterPath()
        return b
    
    @ioc.entity
    def assemblyResourcesGateway():
        b = Assembly('Gateway REST resources')
        b.add(assemblyResources())
        b.replace(encoderPathResource(), encoderPathResourceGateway())
        return b
    
    @ioc.entity
    def resourcesRouterGateway():
        b = RoutingByPathHandler()
        b.assembly = assemblyResourcesGateway()
        b.pattern = server_pattern_resources()
        return b
    
    # ----------------------------------------------------------------
    
    def isInternal():
        '''
        Auxiliar function.
        '''
        if server_provide_gateway() != GATEWAY_INTERNAL: return False
        if not server_provide_resources():
            raise SetupError('Cannot configure internal gateway because the REST resources is not enabled')
        return True
    
    @ioc.before(assemblyRESTRequest)
    def updateAssemblyRESTRequestForResources():
        if isInternal(): assemblyRESTRequest().add(resourcesRouter())
                
    @ioc.before(assemblyForward)
    def updateAssemblyForwardForResources():
        if isInternal():
            assemblyForward().add(resourcesRouterGateway())
            if server_provide_errors(): assemblyForward().add(errorsRouter(), after=resourcesRouterGateway())
    
    @ioc.after(updateAssemblyServerForResources)
    def updateAssemblyServerForGatewayInternal():
        if isInternal(): assemblyServer().add(gatewayRouter(), before=resourcesRouter())
