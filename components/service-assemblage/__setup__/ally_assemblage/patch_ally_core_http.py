'''
Created on Feb 8, 2013

@package: service assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server patch configuration when used internally with REST.
'''

from ..ally_http.server import assemblyServer, notFoundRouter
from .processor import assemblyForward, server_provide_assemblage, \
    ASSEMBLAGE_INTERNAL, ASSEMBLAGE_EXTERNAL, updateAssemblyForward, \
    assemblyRESTRequest
from ally.container import ioc, support
from ally.container.error import SetupError
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_core_http
except ImportError:
    log.info('No REST core available, you need to configure an external request assembly for assemblages')
    
    @ioc.before(assemblyForward)
    def updateAssemblyForwardForResources():
        if server_provide_assemblage() == ASSEMBLAGE_INTERNAL:
            raise SetupError('Cannot configure internal assemblage because the ally core http component is not present')
else: 
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------

    from ..ally_core_http.server import resourcesRouter, server_provide_resources, server_provide_errors, \
    updateAssemblyServerForResources
    
    # ----------------------------------------------------------------
    
    def isInternal():
        '''
        Auxiliar function.
        '''
        if server_provide_assemblage() != ASSEMBLAGE_INTERNAL: return False
        if not server_provide_resources():
            raise SetupError('Cannot configure internal assemblage because the REST resources is not enabled')
        return True
    
    @ioc.before(server_provide_errors)
    def disableServerProvideErrors():
        if server_provide_assemblage() == ASSEMBLAGE_EXTERNAL and server_provide_errors():
            log.warn('Cannot use errors with this external assemblage proxy, disabling errors providing')
            support.force(server_provide_errors, False)
            
    @ioc.before(server_provide_resources)
    def disableServerProvideResources():
        if server_provide_assemblage() == ASSEMBLAGE_EXTERNAL and server_provide_resources():
            log.warn('Cannot use REST resources with this external assemblage proxy, disabling REST resources')
            support.force(server_provide_resources, False)
    
    @ioc.before(assemblyRESTRequest)
    def updateAssemblyRESTRequestForResources():
        if isInternal(): assemblyRESTRequest().add(resourcesRouter())
    
    @ioc.after(updateAssemblyForward)
    def updateAssemblyForwardForResources():
        if isInternal(): assemblyForward().add(resourcesRouter(), before=notFoundRouter())
    
    @ioc.after(updateAssemblyServerForResources)
    def updateAssemblyServerForAssemblageInternal():
        if isInternal(): assemblyServer().remove(resourcesRouter())
