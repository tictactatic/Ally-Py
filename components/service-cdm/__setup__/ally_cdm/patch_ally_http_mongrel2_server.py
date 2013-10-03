'''
Created on Nov 23, 2011

@package: service CDM
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the Mongrel2 web server plugins patch for the cdm.
'''

from ..ally_cdm.server import server_provide_content
from ..ally_http.server import server_type
from ally.container import ioc, support
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_http_mongrel2_server # @UnusedImport
except ImportError: log.info('No mongrel2 available thus skip the CDM patching')
else:
    ioc.doc(server_provide_content, '''
    !Attention, if the mongrel2 server is selected this option will always be "false"
    ''')
    
    @ioc.before(server_provide_content, auto=False)
    def server_provide_content_force():
        if server_type() == 'mongrel2': support.force(server_provide_content, False)
