'''
Created on Jan 25, 2013

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup patch when the server is run with ally core http.
'''

from ..ally_http import server_type
from ..ally_http.processor import headerDecodeRequest, contentLengthDecode
from .processor import asyncoreContent
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_gateway
except ImportError: log.info('No gateway service available thus skip the patching specific for asyncore')
else:
    ally_gateway = ally_gateway  # Just to avoid the import warning
    # ----------------------------------------------------------------

    from ..ally_gateway.processor import updateAssemblyRESTRequestForExternal, updateAssemblyForwardForExternal, \
    server_provide_gateway, assemblyRESTRequest, assemblyForward, externalForward, GATEWAY_EXTERNAL
    
    # ----------------------------------------------------------------
    
    @ioc.after(updateAssemblyRESTRequestForExternal)
    def updateAssemblyRESTRequestForHTTPAsyncore():
        if server_type() == 'asyncore' and server_provide_gateway() == GATEWAY_EXTERNAL:
            assemblyRESTRequest().add(headerDecodeRequest(), contentLengthDecode(), asyncoreContent(), before=externalForward())
            
    @ioc.after(updateAssemblyForwardForExternal)
    def updateAssemblyForwardForHTTPAsyncore():
        if server_type() == 'asyncore' and server_provide_gateway() == GATEWAY_EXTERNAL:
            assemblyForward().add(headerDecodeRequest(), contentLengthDecode(), asyncoreContent(), before=externalForward())
