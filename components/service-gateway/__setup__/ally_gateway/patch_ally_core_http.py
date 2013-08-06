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
from ally.http.impl.processor.router_by_path import RoutingByPathHandler
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_core_http  # @UnusedImport
except ImportError:
    log.info('No REST core available, you need to configure an external request assembly for gateway')
    
    @ioc.before(assemblyRESTRequest, assemblyForward)
    def updateAssemblyForResources():
        if server_provide_gateway() == GATEWAY_INTERNAL:
            raise SetupError('Cannot configure internal gateway because the ally core http component is not present')
    
else: 
    from ..ally_core_http.server import resourcesRouter, server_provide_resources, updateAssemblyServerForResources, \
    errorsRouter, server_provide_errors, root_uri_resources
    from ..ally_core_http.processor import assemblyResources
    
    @ioc.entity
    def resourcesRouterGateway():
        b = RoutingByPathHandler()
        b.assembly = assemblyResources()
        b.rootURI = root_uri_resources()
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
