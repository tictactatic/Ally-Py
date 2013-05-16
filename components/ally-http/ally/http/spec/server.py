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
import abc

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
        
# --------------------------------------------------------------------

class IEncoderPath(metaclass=abc.ABCMeta):
    '''
    Provides the path encoding.
    '''
    __slots__ = ()

    @abc.abstractmethod
    def encode(self, path, **keyargs):
        '''
        Encodes the provided path to a full request path.
        
        @param path: object
            The path to be encoded, the type depends on the implementation.
        @param keyargs: key arguments
            Key arguments containing specific data that can be handled by the encoder, if unknown or invalid data is provided 
            then the encoder has the duty to report that.
        @return: string
            The full compiled request path.
        '''
        
    @abc.abstractmethod
    def encodePattern(self, path, **keyargs):
        '''
        Encodes the provided path to a pattern path that can be used as regex to identify paths corresponding to the provided
        path.
        
        @param path: object
            The path to be encoded as a pattern, the type depends on the implementation.
        @param keyargs: key arguments
            Key arguments containing specific data that can be handled by the encoder, if unknown or invalid data is provided 
            then the encoder has the duty to report that.
        @return: string
            The path pattern.
        '''
