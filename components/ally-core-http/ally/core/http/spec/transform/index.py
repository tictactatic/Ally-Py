'''
Created on Apr 17, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides HTTP specifications for indexes. 
'''

from ally.core.impl.processor.render.xml import createXMLAttrsInjectMarkers
from ally.core.spec.transform.index import ACTION_CAPTURE
from ally.support.util import immut

# --------------------------------------------------------------------

NAME_URL = 'URL'  # The marker name for HTTP URL.

# --------------------------------------------------------------------

GROUP_URL = 'URL'  # The group name for URL reference.
GROUP_ERROR = 'error'  # The group name for errors occurred while fetching URLs.

ERROR_STATUS = 'ERROR'  # The attribute name for error status.
ERROR_MESSAGE = 'ERROR_TEXT'  # The attribute name for error message.

MARKER_VALUE = '*'  # The marker to be used for injecting the attribute value.

# --------------------------------------------------------------------

# Provides the URL markers definitions.
URL_MARKERS = {
               NAME_URL: immut(group=GROUP_URL, action=ACTION_CAPTURE),
               }
# We populate the error markers, the error attributes have the place holder '*' for injecting values.
URL_MARKERS.update(createXMLAttrsInjectMarkers(GROUP_ERROR, {ERROR_STATUS:MARKER_VALUE, ERROR_MESSAGE:MARKER_VALUE}))
