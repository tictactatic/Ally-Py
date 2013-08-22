'''
Created on Jun 1, 2012

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides HTTP server specification.
'''

from .headers import HeadersRequire
from ally.design.processor.attribute import requires, optional, defines, \
    definesIf
from ally.design.processor.context import Context
from ally.support.util_io import IInputStream
from collections import Iterable
from ally.design.processor.execution import Processing

# --------------------------------------------------------------------

# HTTP scheme/protocol.
HTTP = 'http'

# HTTP methods.
HTTP_GET = 'GET'
HTTP_DELETE = 'DELETE'
HTTP_POST = 'POST'
HTTP_PUT = 'PUT'
HTTP_OPTIONS = 'OPTIONS'

# --------------------------------------------------------------------

class RequestHTTP(Context):
    '''
    Context for HTTP request data. 
    '''
    # ---------------------------------------------------------------- Defined
    clientIP = definesIf(str, doc='''
    @rtype: string
    The client IP that made the request.
    ''')
    scheme = defines(str, doc='''
    @rtype: string
    The scheme URI protocol name to be used for the response.
    ''')
    method = defines(str, doc='''
    @rtype: string
    The method name of the request.
    ''')
    uri = defines(str, doc='''
    @rtype: string
    The relative request URI.
    ''')
    headers = definesIf(dict, doc='''
    @rtype: dictionary{string, string}
    The raw headers.
    ''')
    parameters = definesIf(list, doc='''
    @rtype: list[tuple(string, string)]
    The parameters of the request.
    ''')

class RequestContentHTTP(Context):
    '''
    Context for HTTP request content data. 
    '''
    # ---------------------------------------------------------------- Defined
    source = definesIf(IInputStream, doc='''
    @rtype: IInputStream
    The source for the request content.
    ''')

class ResponseHTTP(HeadersRequire):
    '''
    Context for HTTP response data. 
    '''
    # ---------------------------------------------------------------- Optional
    code = optional(str, doc='''
    @rtype: string
    The response code message.
    ''')
    text = optional(str, doc='''
    @rtype: string
    The response text message (a short message).
    ''')
    # ---------------------------------------------------------------- Required
    status = requires(int, doc='''
    @rtype: integer
    The response status code.
    ''')

class ResponseContentHTTP(Context):
    '''
    Context for HTTP response content data. 
    '''
    # ---------------------------------------------------------------- Required
    source = optional(IInputStream, Iterable, doc='''
    @rtype: IInputStream|Iterable
    The source for the response content.
    ''')
