'''
Created on Apr 12, 2013

@package: service assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server patch configuration when used internally with gateway service.
'''

from ..ally_http.server import assemblyServer
from .processor import assemblyForward, updateAssemblyForward, notFoundRouter, \
    server_provide_assemblage, ASSEMBLAGE_EXTERNAL, ASSEMBLAGE_INTERNAL
from ally.container import ioc
from ally.container.error import SetupError
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_gateway  # @UnusedImport
except ImportError: log.info('No gateway service available, no need to patch it')
else: 
    from ..ally_gateway.server import gatewayRouter, server_provide_gateway, updateAssemblyServerForGatewayExternal
    from ..ally_gateway.processor import GATEWAY_EXTERNAL, GATEWAY_INTERNAL
    
    @ioc.after(updateAssemblyForward)
    def updateAssemblyForwardForGateway():
        if server_provide_gateway() == GATEWAY_EXTERNAL and server_provide_assemblage() == ASSEMBLAGE_EXTERNAL:
            assemblyForward().add(gatewayRouter(), before=notFoundRouter())
            
    @ioc.after(updateAssemblyServerForGatewayExternal)
    def removeAssemblyServerForGatewayExternal():
        if server_provide_gateway() == GATEWAY_EXTERNAL and server_provide_assemblage() == ASSEMBLAGE_EXTERNAL:
            assemblyServer().remove(gatewayRouter())

    try: from .. import ally_core_http  # @UnusedImport
    except ImportError:
        @ioc.before(assemblyForward)
        def updateAssemblyForwardForGatewayInternal():
            if server_provide_gateway() == GATEWAY_INTERNAL:
                if server_provide_assemblage() == ASSEMBLAGE_EXTERNAL:
                    raise SetupError('Cannot configure internal gateway with external assemblage')
                elif server_provide_assemblage() == ASSEMBLAGE_INTERNAL:
                    raise SetupError('Cannot configure internal assemblage because the ally core http component is not present')
    else: 
        from ..ally_gateway.patch_ally_core_http import updateAssemblyServerForGatewayInternal
        from .patch_ally_core_http import updateAssemblyForwardForResources, resourcesRouter, isInternal
    
        @ioc.after(updateAssemblyForwardForResources)
        def updateAssemblyForwardForGatewayInternal():
            if server_provide_gateway() == GATEWAY_INTERNAL and isInternal():
                assemblyForward().add(gatewayRouter(), before=resourcesRouter())
        
        ioc.cancel(updateAssemblyServerForGatewayInternal)  # We need to cancel the server assembly adding.
