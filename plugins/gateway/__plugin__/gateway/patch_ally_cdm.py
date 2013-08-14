'''
Created on Feb 19, 2013

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ally cdm setup patch, basically at this point we allow all content.
'''

from .service import asPattern, defaultGateways
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from __setup__ import ally_cdm  # @UnusedImport
except ImportError: log.info('No ally CDM service available, thus no need to create configurations based on it')
else:
    from __setup__.ally_cdm.server import root_uri_content, server_provide_content
    from ally.http.spec.server import HTTP_GET
    
    @ioc.before(defaultGateways)
    def updateGatewayWithCDM():
        if server_provide_content():
            defaultGateways().extend([
            {
             'Pattern': asPattern(root_uri_content()),
             'Methods': [HTTP_GET],
             },
                                      ])
