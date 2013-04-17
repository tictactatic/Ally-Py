'''
Created on Jan 23, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblage service setup patch.
'''

from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from __setup__ import ally_assemblage
    from __setup__ import ally_core_http
except ImportError: log.info('No assemblage service available, thus no need to publish the assemblage data')
else:
    ally_assemblage = ally_assemblage  # Just to avoid the import warning
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------
    
    from __setup__.ally_assemblage.processor import assemblage_marker_uri
    from __setup__.ally_core_http.processor import root_uri_resources
    
    @ioc.replace(assemblage_marker_uri)
    def assemblage_marker_uri_internal():
        '''
        The assemblage marker URI.
        '''
        return root_uri_resources() % 'Assemblage/Marker'
