'''
Created on Jun 30, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the codes to be used for the server responses.
'''

from ally.design.processor.attribute import defines, definesIf
from ally.design.processor.context import Context

# --------------------------------------------------------------------

class CodedHTTP(Context):
    '''
    Context for coded. 
    '''
    # ---------------------------------------------------------------- Defines
    code = defines(str, doc='''
    @rtype: string
    The unique code associated with the context.
    ''')
    status = defines(int, doc='''
    @rtype: integer
    The HTTP status code.
    ''')
    isSuccess = definesIf(bool, doc='''
    @rtype: boolean
    True if the context is in success mode, False otherwise.
    ''')
    
# --------------------------------------------------------------------
        
class CodeHTTP:
    '''
    Contains the HTTP response code.
    '''
    __slots__ = ('code', 'status', 'isSuccess')

    def __init__(self, code, status):
        '''
        Constructs the code.
        
        @param code: string
            The code text corresponding to this code.
        @param status: integer
            The HTTP status code.
        '''
        assert isinstance(code, str), 'Invalid code %s' % code
        assert isinstance(status, int), 'Invalid status %s' % status
        self.code = code
        self.status = status
        self.isSuccess = isSuccess(status)
        
    def set(self, context):
        '''
        Set the code on the provided context.
        
        @param context: Context
            The context to set the code to.
        '''
        assert isinstance(context, CodedHTTP), 'Invalid context %s' % context
        context.code = self.code
        context.status = self.status
        if CodedHTTP.isSuccess in context: context.isSuccess = self.isSuccess

def isSuccess(status):
    '''
    Checks if the status provided is a success status.
    
    @param status: integer
        The status code to check if is for a successful operation.
    @return: boolean
        True if the status is a success status, False otherwise.
    '''
    assert isinstance(status, int), 'Invalid status %s' % status
    return int(status / 100) == 2
    
# --------------------------------------------------------------------
# Response codes.

PATH_NOT_FOUND = CodeHTTP('Not found', 404)  # HTTP code 404 Not Found
PATH_ERROR = CodeHTTP('Path error', 404)  # HTTP code 404 Not Found
PATH_FOUND = CodeHTTP('OK', 200)  # HTTP code 200 OK

METHOD_NOT_AVAILABLE = CodeHTTP('Method not allowed', 405)  # HTTP code 405 Method Not Allowed

MISSING_SLASH = CodeHTTP('Missing trailing slash', 400)  # HTTP code 400 Bad Request
CONTENT_LENGHT_ERROR = CodeHTTP('Length required ', 411)  # HTTP code 411 length required 

BAD_REQUEST = CodeHTTP('Bad Request', 400)  # HTTP code 400 Bad Request

HEADER_ERROR = CodeHTTP('Invalid header', 400)  # HTTP code 400 Bad Request

INTERNAL_ERROR = CodeHTTP('Internal error', 500)  # HTTP code 500 Internal Server Error

# --------------------------------------------------------------------
# Response gateway HTTP codes.

SERVICE_UNAVAILABLE = CodeHTTP('Service Unavailable', 503)  # HTTP code 503 Service Unavailable

BAD_GATEWAY = CodeHTTP('Bad Gateway', 502)  # HTTP code 502 Bad Gateway

UNAUTHORIZED_ACCESS = CodeHTTP('Unauthorized access', 401)  # HTTP code 401 Unauthorized access

INVALID_AUTHORIZATION = CodeHTTP('Invalid authorization', 401)  # HTTP code 401 Unauthorized access

FORBIDDEN_ACCESS = CodeHTTP('Forbidden access', 403)  # HTTP code 403 Forbidden access
