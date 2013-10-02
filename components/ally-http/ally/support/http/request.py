'''
Created on Apr 30, 2013

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides request dispatching support.
'''

from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines
from ally.design.processor.execution import Processing, FILL_ALL
from ally.http.spec.codes import isSuccess
from ally.http.spec.server import HTTP, RequestHTTP, ResponseContentHTTP, \
    ResponseHTTP, HTTP_GET, HTTP_OPTIONS, RequestContentHTTP
from ally.support.util_io import IInputStream, IClosable
from io import BytesIO
from urllib.parse import urlparse, parse_qsl
import codecs
import json
import logging
from collections import namedtuple

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class RequesterOptions:
    '''
    Makes OPTIONS headers requests. 
    '''
    
    def __init__(self, assembly, scheme=HTTP):
        '''
        Create the options request handler.
        
        @param assembly: Assembly
            The assembly used for delivering the request.
        '''
        assert isinstance(scheme, str), 'Invalid scheme %s' % scheme
        
        self._processing = assembly.create(request=RequestHTTP, requestCnt=RequestContentHTTP,
                                           response=ResponseHTTP, responseCnt=ResponseContentHTTP)
        self._scheme = scheme
        
    def request(self, uri):
        '''
        Request the OPTIONS headers for URI.
        
        @param uri: string
            The URI to call, parameters are allowed.
        @return: dictionary{string: string}|None
            The OPTIONS header or None if OPTIONS has not been delivered successful.
        '''
        assert isinstance(uri, str), 'Invalid URI %s' % uri
        
        proc = self._processing
        assert isinstance(proc, Processing)
        
        request = proc.ctx.request()
        assert isinstance(request, RequestHTTP), 'Invalid request %s' % request
        
        request.scheme, request.method = self._scheme, HTTP_OPTIONS
        request.uri = urlparse(uri).path.lstrip('/')
        request.parameters = []
        
        arg = proc.execute(FILL_ALL, request=request)
        response, responseCnt = arg.response, arg.responseCnt
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        
        # We need to ensure that we close the response source.
        if ResponseContentHTTP.source in responseCnt and isinstance(responseCnt.source, IClosable): responseCnt.source.close()
        
        if isSuccess(response.status) and ResponseHTTP.headers in response:
            return response.headers
        
        if __debug__:
            if ResponseHTTP.text in response and response.text: text = response.text
            elif ResponseHTTP.code in response and response.code: text = response.code
            else: text = None
            log.error('Cannot get OPTIONS from \'%s\', with response %s %s', request.uri, response.status, text)

# --------------------------------------------------------------------

class RequesterGetJSON:
    '''
    Makes GET requests for JSON response objects. 
    '''
    
    class Request(RequestHTTP):
        '''
        The request dispatch context.
        '''
        # ---------------------------------------------------------------- Defined
        accTypes = defines(list)
        accCharSets = defines(list)
        
    Error = namedtuple('Error', ['status', 'text'])
    # The error tuple used for providing error details.
    
    def __init__(self, assembly, scheme=HTTP, contentType='json', encoding='utf-8'):
        '''
        Create the get json request handler.
        
        @param assembly: Assembly
            The assembly used for delivering the request.
        @param scheme: string
            The scheme to be used in dispatching the request.
        @param contentType: string
            The json content type to be sent for the object requests.
        @param encoding: string
            The json encoding to be sent for the object requests.
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        assert isinstance(scheme, str), 'Invalid scheme %s' % scheme
        assert isinstance(contentType, str), 'Invalid content type %s' % contentType
        assert isinstance(encoding, str), 'Invalid encoding %s' % encoding
        
        self._processing = assembly.create(request=RequesterGetJSON.Request, requestCnt=RequestContentHTTP,
                                           response=ResponseHTTP, responseCnt=ResponseContentHTTP)
        self._scheme = scheme
        self._contentType = contentType
        self._encoding = encoding
        
    def request(self, uri, details=False):
        '''
        Request the JSON object for URI.
        
        @param uri: string
            The URI to call, parameters are allowed.
        @param details: boolean
            If True will provide beside the JSON object also the response status and text.
        @return: object|tuple(object, integer, string)
            Provides the loaded JSON object if details is False, otherwise a tuple containing as the first entry the JSON
            object, None if the object cannot be fetched, on the second position the response status and on the last
            position the response text.
        '''
        assert isinstance(uri, str), 'Invalid URI %s' % uri
        assert isinstance(details, bool), 'Invalid details flag %s' % details
        
        proc = self._processing
        assert isinstance(proc, Processing)
        
        request = proc.ctx.request()
        assert isinstance(request, RequesterGetJSON.Request), 'Invalid request %s' % request
    
        url = urlparse(uri)
        request.scheme, request.method = self._scheme, HTTP_GET
        request.uri = url.path.lstrip('/')
        request.parameters = parse_qsl(url.query, True, False)
        request.accTypes = [self._contentType]
        request.accCharSets = [self._encoding]
        
        arg = proc.execute(FILL_ALL, request=request)
        response, responseCnt = arg.response, arg.responseCnt
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        
        if ResponseHTTP.text in response and response.text: text = response.text
        elif ResponseHTTP.code in response and response.code: text = response.code
        else: text = None
        if ResponseContentHTTP.source not in responseCnt or responseCnt.source is None or not isSuccess(response.status):
            assert log.error('Cannot get JSON from \'%s\', with response %s %s', request.uri, response.status, text) or True
            if details: return None, RequesterGetJSON.Error(response.status, text)
            return
        
        if isinstance(responseCnt.source, IInputStream):
            source = responseCnt.source
        else:
            source = BytesIO()
            for bytes in responseCnt.source: source.write(bytes)
            source.seek(0)
        
        jobj = json.load(codecs.getreader(self._encoding)(source))
        if isinstance(source, IClosable): source.close()  # We need to ensure that we close the response source.
        if details: return jobj, RequesterGetJSON.Error(response.status, text)
        return jobj
