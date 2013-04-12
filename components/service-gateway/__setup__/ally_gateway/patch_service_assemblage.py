'''
Created on Apr 12, 2013

@package: service gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server patch configuration when used internally with assemblage service.
'''

from .server import gatewayRouter
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_assemblage, ally_core_http
except ImportError: log.info('No assemblage available, no need to patch it')
else: 
    ally_assemblage = ally_assemblage  # Just to avoid the import warning
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------
    
    from .patch_ally_core_http import updateAssemblyServerForGatewayInternal, isInternal
    from ..ally_assemblage.processor import assemblyForward
    from ..ally_core_http.server import resourcesRouter

    @ioc.replace(updateAssemblyServerForGatewayInternal)
    def updateAssemblyServerForGatewayInternalWithAssemblage():
        if isInternal(): assemblyForward().add(gatewayRouter(), before=resourcesRouter())
