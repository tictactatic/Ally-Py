'''
Created on Jan 23, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblage service setup patch.
'''

from ally.container import ioc
from ally.support.api.util_service import nameForModel
from indexing.api.domain_indexing import DOMAIN
from indexing.api.indexing import Block
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from __setup__ import ally_assemblage  # @UnusedImport
    from __setup__ import ally_core_http  # @UnusedImport
except ImportError: log.info('No assemblage service available, thus no need to publish the assemblage data')
else:
    from __setup__.ally_assemblage.processor import assemblage_indexes_uri
    from __setup__.ally_core_http.server import root_uri_resources
    
    @ioc.replace(assemblage_indexes_uri)
    def assemblage_indexes_uri_internal():
        '''
        The assemblage indexes URI.
        '''
        return ''.join((root_uri_resources(), '/', DOMAIN, nameForModel(Block), '/%s'))
