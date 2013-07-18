'''
Created on Jul 17, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides aid contexts and support functions that are generally used.
'''

from ally.http.spec.codes import CodedHTTP
from ally.core.impl.processor.base import ErrorResponse

# --------------------------------------------------------------------

class ErrorResponseHTTP(ErrorResponse, CodedHTTP):
    '''
    The error response for HTTP context.
    '''
