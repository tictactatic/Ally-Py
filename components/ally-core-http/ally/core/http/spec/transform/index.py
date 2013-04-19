'''
Created on Apr 17, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides HTTP specifications for indexes. 
'''

from ally.core.impl.processor.render.xml import createXMLAttrsInjectMarkers, \
    createXMLContentInjectMarker
from ally.core.spec.transform.index import ACTION_CAPTURE, PLACE_HOLDER_CONTENT

# --------------------------------------------------------------------

NAME_URL = 'URL'  # The marker name for HTTP URL.

# --------------------------------------------------------------------

GROUP_URL = 'URL'  # The group name for URL reference.
GROUP_ERROR = 'error'  # The group name for errors occurred while fetching URLs.

CONTENT_CLOB = 'clob'  # The name for character blobs injection from reference URLs.
ATTR_ERROR_STATUS = 'ERROR'  # The attribute name for error status.
ATTR_ERROR_MESSAGE = 'ERROR_TEXT'  # The attribute name for error message.

# --------------------------------------------------------------------

# Provides the URL markers definitions.
HTTP_MARKERS = {
                NAME_URL: dict(group=GROUP_URL, action=ACTION_CAPTURE),
                }
# We populate the error markers, the error attributes will have an empty value signaling the proxy server to
# fill in the values.
HTTP_MARKERS.update(createXMLAttrsInjectMarkers(GROUP_ERROR, {ATTR_ERROR_STATUS:PLACE_HOLDER_CONTENT,
                                                              ATTR_ERROR_MESSAGE:PLACE_HOLDER_CONTENT}))
# We populate the clob markers for injecting character content, the content will have an empty value signaling
# the proxy server to fill in the values.
HTTP_MARKERS.update(createXMLContentInjectMarker(CONTENT_CLOB, PLACE_HOLDER_CONTENT))
