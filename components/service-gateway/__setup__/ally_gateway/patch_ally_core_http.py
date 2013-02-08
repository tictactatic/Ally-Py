'''
Created on Feb 8, 2013

@package: service CDM
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server patch configuration when used with rest server.
'''

from ..ally_http.server import assemblyServer
from .processor import assemblyRequest
from .server import server_provide_gateway, updateAssemblyServerForGateway, \
    gatewayRouter, updateAssemblyRequest
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------
    
try: from .. import ally_core_http
except ImportError: log.info('No REST core available, you need to configure an external request assembly for gateway')
else: 
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------

    from ..ally_core_http.server import resourcesRouter, server_provide_rest, server_deliver_errors, \
        updateAssemblyServerForResources, errorsRouter
    
    ioc.cancel(updateAssemblyServerForGateway)
    
    @ioc.before(updateAssemblyRequest)
    def updateAssemblyRequestForResources():
        if server_provide_gateway():
            if server_provide_rest(): assemblyRequest().add(resourcesRouter())
            if server_deliver_errors(): assemblyRequest().add(errorsRouter(), after=resourcesRouter())
    
    @ioc.after(updateAssemblyServerForResources)
    def updateAssemblyServerForGateway():
        if server_provide_gateway():
            assemblyServer().add(gatewayRouter(), before=resourcesRouter())
