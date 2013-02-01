'''
Created on Jun 30, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the codes to be used for the server responses.
'''

from ally.support.util import tupleify

# --------------------------------------------------------------------

@tupleify('code', 'status', 'isSuccess')
class CodeHTTP:
    '''
    Contains the HTTP response code.
    '''

    def __init__(self, code, status, isSuccess):
        '''
        Constructs the code.
        
        @param code: string
            The code text corresponding to this code.
        @param status: integer
            The HTTP status code.
        @param isSuccess: boolean
            Flag indicating if the code is a fail or success code.
        '''
        assert isinstance(code, str), 'Invalid code %s' % code
        assert isinstance(status, int), 'Invalid status %s' % status
        assert isinstance(isSuccess, bool), 'Invalid success flag %s' % isSuccess
        self.code = code
        self.status = status
        self.isSuccess = isSuccess
        
# --------------------------------------------------------------------
# Response codes.

PATH_NOT_FOUND = CodeHTTP('Invalid path', 404, False)  # HTTP code 404 Not Found
PATH_FOUND = CodeHTTP('Path found', 200, True)  # HTTP code 200 OK

METHOD_NOT_AVAILABLE = CodeHTTP('Method not available', 501, False)  # HTTP code 501 Unsupported method

HEADER_ERROR = CodeHTTP('Invalid header', 400, False)  # HTTP code 400 Bad Request

INTERNAL_ERROR = CodeHTTP('Internal error', 500, False)  # HTTP code 500 Internal Server Error
