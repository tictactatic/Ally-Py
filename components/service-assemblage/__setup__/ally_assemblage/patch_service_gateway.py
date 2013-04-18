'''
Created on Apr 12, 2013

@package: service assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server patch configuration when used internally with gateway service.
'''

from .processor import assemblyForward
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_gateway, ally_core_http
except ImportError: log.info('No gateway service available, no need to patch it')
else: 
    ally_gateway = ally_gateway  # Just to avoid the import warning
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------
    
    from ..ally_gateway.server import gatewayRouter
    from ..ally_gateway.patch_ally_core_http import isInternal, updateAssemblyServerForGatewayInternal
    from .patch_ally_core_http import updateAssemblyForwardForResources

    @ioc.before(updateAssemblyForwardForResources)
    def updateAssemblyForwardForGateway():
        if isInternal(): assemblyForward().add(gatewayRouter())
    
    ioc.cancel(updateAssemblyServerForGatewayInternal)  # We need to cancel the server assembly adding.
