'''
Created on Apr 30, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides HTTP headers support.
'''

from ally.http.spec.headers import HeaderCmx, HeaderRaw
        
# --------------------------------------------------------------------

CONTENT_DISPOSITION = HeaderCmx('Content-Disposition', True)
# Content disposition as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec19.html chapter 19.5.1
LOCATION = HeaderRaw('Location')
# Location as described at: http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html chapter 14.30

# --------------------------------------------------------------------

CONTENT_TYPE_ATTR_BOUNDARY = 'boundary'
# The name of the CONTENT_TYPE attribute where the boundary for the multi part is placed.
CONTENT_DISPOSITION_ATTR_FILENAME = 'filename'
# The name of the CONTENT_DISPOSITION attribute where the filename parameter from a multipart form is placed.
