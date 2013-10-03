'''
Created on Jan 25, 2013

@package: service gateway
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup patch when the server is asyncore.
'''

from ..ally_http.processor import contentLengthDecode
from ..ally_http.server import server_type
from .processor import updateAssemblyForwardForExternal, server_provide_gateway, \
    assemblyForward, externalForward, GATEWAY_EXTERNAL
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_http_asyncore_server # @UnusedImport
except ImportError: log.info('No asyncore available thus skip the gateway patching')
else:
    from ..ally_http_asyncore_server.processor import asyncoreContent
    from ..ally_http_asyncore_server.server import SERVER_ASYNCORE
            
    @ioc.after(updateAssemblyForwardForExternal)
    def updateAssemblyForwardForHTTPAsyncore():
        if server_type() == SERVER_ASYNCORE and server_provide_gateway() == GATEWAY_EXTERNAL:
            assemblyForward().add(contentLengthDecode(), asyncoreContent(), before=externalForward())
