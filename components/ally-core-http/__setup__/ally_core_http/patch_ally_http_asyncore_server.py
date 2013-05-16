'''
Created on Jan 25, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup patch when the server is asyncore.
'''

from ..ally_http import server_type
from .processor import updateAssemblyResources, assemblyResources, \
    parsingMultiPart
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_http_asyncore_server
except ImportError: log.info('No asyncore available thus skip the resources patching')
else:
    ally_http_asyncore_server = ally_http_asyncore_server  # Just to avoid the import warning
    # ----------------------------------------------------------------

    from ..ally_http_asyncore_server.processor import asyncoreContent
    from ..ally_http_asyncore_server.server import SERVER_ASYNCORE
    
    @ioc.after(updateAssemblyResources)
    def updateAssemblyResourcesForHTTPAsyncore():
        if server_type() == SERVER_ASYNCORE:
            assemblyResources().add(asyncoreContent(), before=parsingMultiPart())
