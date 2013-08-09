'''
Created on Apr 30, 2013

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides request dispatching support.
'''

from ally.design.processor.attribute import defines
from ally.design.processor.execution import Processing, FILL_ALL
from ally.http.spec.codes import isSuccess
from ally.http.spec.server import HTTP, RequestHTTP, ResponseContentHTTP, \
    ResponseHTTP, HTTP_GET, HTTP_OPTIONS
from ally.support.util_io import IInputStream, IClosable
from io import BytesIO
from urllib.parse import urlparse, parse_qsl
import codecs
import json
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class RequestDispatch(RequestHTTP):
    '''
    The request dispatch context.
    '''
    # ---------------------------------------------------------------- Defined
    accTypes = defines(list)
    accCharSets = defines(list)

# --------------------------------------------------------------------

def obtainOPTIONS(processing, uri, scheme=HTTP):
    '''
    Obtains the options headers for URI.
    
    @param processing: Processing
        The processing used for delivering the request.
    @param uri: string
        The URI to call, parameters are allowed.
    @return: dictionary{string: string}|None
        The OPTIONS header or None if OPTIONS has not been delivered successful.
    '''
    assert isinstance(processing, Processing), 'Invalid processing %s' % processing
    assert isinstance(uri, str), 'Invalid URI %s' % uri
    
    request = processing.ctx.request()
    assert isinstance(request, RequestHTTP), 'Invalid request %s' % request
    
    request.scheme, request.method = scheme, HTTP_OPTIONS
    request.uri = urlparse(uri).path.lstrip('/')
    request.parameters = []
    
    arg = processing.execute(FILL_ALL, request=request)
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

def obtainJSON(processing, uri, details=False, scheme=HTTP, mimeTypeJson='json', encodingJson='utf-8'):
    '''
    Obtains the JSON object for URI.
    
    @param processing: Processing
        The processing used for delivering the request.
    @param uri: string
        The URI to call, parameters are allowed.
    @param details: boolean
        If True will provide beside the JSON object also the response status and text.
    @param scheme: string
        The scheme to be used in dispatching the request.
    @param mimeTypeJson: string
        The json mime type to be sent for the object requests.
    @param encodingJson: string
        The json encoding to be sent for the object requests.
    @return: object|tuple(object, integer, string)
        Provides the loaded JSON object if details is False, otherwise a tuple containing as the first entry the JSON
        object, None if the object cannot be fetched, on the second position the response status and on the last
        position the response text.
    '''
    assert isinstance(processing, Processing), 'Invalid processing %s' % processing
    assert isinstance(uri, str), 'Invalid URI %s' % uri
    assert isinstance(details, bool), 'Invalid details flag %s' % details
    
    request = processing.ctx.request()
    assert isinstance(request, RequestDispatch), 'Invalid request %s' % request

    url = urlparse(uri)
    request.scheme, request.method = scheme, HTTP_GET
    request.uri = url.path.lstrip('/')
    request.parameters = parse_qsl(url.query, True, False)
    request.accTypes = [mimeTypeJson]
    request.accCharSets = [encodingJson]
    
    arg = processing.execute(FILL_ALL, request=request)
    response, responseCnt = arg.response, arg.responseCnt
    assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
    assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
    
    if ResponseHTTP.text in response and response.text: text = response.text
    elif ResponseHTTP.code in response and response.code: text = response.code
    else: text = None
    if ResponseContentHTTP.source not in responseCnt or responseCnt.source is None or not isSuccess(response.status):
        assert log.error('Cannot get JSON from \'%s\', with response %s %s', request.uri, response.status, text) or True
        if details: return None, response.status, text
        return
    
    if isinstance(responseCnt.source, IInputStream):
        source = responseCnt.source
    else:
        source = BytesIO()
        for bytes in responseCnt.source: source.write(bytes)
        source.seek(0)
    
    jobj = json.load(codecs.getreader(encodingJson)(source))
    if isinstance(source, IClosable): source.close()  # We need to ensure that we close the response source.
    if details: return jobj, response.status, text
    return jobj
