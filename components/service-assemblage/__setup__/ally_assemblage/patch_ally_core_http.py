'''
Created on Feb 8, 2013

@package: service CDM
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server patch configuration when used internally with REST.
'''

from ..ally_http.server import assemblyServer
from .processor import assemblyRESTRequest, assemblyForward, \
    server_provide_assemblage, ASSEMBLAGE_INTERNAL
from .server import assemblageRouter
from ally.container import ioc
from ally.container.error import SetupError
import logging


# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_core_http
except ImportError:
    log.info('No REST core available, you need to configure an external request assembly for assemblages')
    
    @ioc.before(assemblyRESTRequest, assemblyForward)
    def updateAssemblyForResources():
        if server_provide_assemblage() == ASSEMBLAGE_INTERNAL:
            raise SetupError('Cannot configure internal assemblage because the ally core http component is not present')
    
else: 
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------

    from ..ally_core_http.server import resourcesRouter, server_provide_resources, updateAssemblyServerForResources
    
    # ----------------------------------------------------------------
    
    @ioc.before(assemblyRESTRequest)
    def updateAssemblyRESTRequestForResources():
        if server_provide_assemblage() == ASSEMBLAGE_INTERNAL:
            if not server_provide_resources():
                raise SetupError('Cannot configure internal assemblage because the REST resources is not enabled')
            assemblyRESTRequest().add(resourcesRouter())
                
    @ioc.before(assemblyForward)
    def updateAssemblyForwardForResources():
        if server_provide_assemblage() == ASSEMBLAGE_INTERNAL:
            if not server_provide_resources():
                raise SetupError('Cannot configure internal assemblage because the REST resources is not enabled')
            assemblyForward().add(resourcesRouter())
    
    @ioc.after(updateAssemblyServerForResources)
    def updateAssemblyServerForGatewayInternal():
        if server_provide_assemblage() == ASSEMBLAGE_INTERNAL:
            if not server_provide_resources():
                raise SetupError('Cannot configure internal assemblage because the REST resources is not enabled')
            assemblyServer().add(assemblageRouter(), before=resourcesRouter())
