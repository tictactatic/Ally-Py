'''
Created on Feb 8, 2013

@package: service CDM
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server patch configuration when used with rest server.
'''

from ..ally_http.server import assemblyServer
from .processor import GATEWAY_INTERNAL, assemblyRESTRequest, assemblyForward
from .server import server_provide_gateway, gatewayRouter
from ally.container import ioc
from ally.container.error import SetupError
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

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

    from ..ally_core_http.server import resourcesRouter, server_provide_rest, updateAssemblyServerForResources, \
    errorsRouter, server_deliver_errors
    
    @ioc.before(assemblyRESTRequest)
    def updateAssemblyRESTRequestForResources():
        if server_provide_gateway() == GATEWAY_INTERNAL:
            if not server_provide_rest():
                raise SetupError('Cannot configure internal gateway because the REST resources is not enabled')
            assemblyRESTRequest().add(resourcesRouter())
            if server_deliver_errors(): assemblyRESTRequest().add(errorsRouter(), after=resourcesRouter())
                
    @ioc.before(assemblyForward)
    def updateAssemblyForwardForResources():
        if server_provide_gateway() == GATEWAY_INTERNAL:
            if not server_provide_rest():
                raise SetupError('Cannot configure internal gateway because the REST resources is not enabled')
            assemblyForward().add(resourcesRouter())
            if server_deliver_errors(): assemblyForward().add(errorsRouter(), after=resourcesRouter())
    
    @ioc.after(updateAssemblyServerForResources)
    def updateAssemblyServerForGatewayInternal():
        if server_provide_gateway() == GATEWAY_INTERNAL:
            if not server_provide_rest():
                raise SetupError('Cannot configure internal gateway because the REST resources is not enabled')
            assemblyServer().add(gatewayRouter(), before=resourcesRouter())
