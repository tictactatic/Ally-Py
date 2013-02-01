'''
Created on Oct 23, 2012

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the WSGI web server support.
'''

from ally.container.ioc import injected
from ally.design.processor import Processing, Assembly, ONLY_AVAILABLE, \
    CREATE_REPORT, Chain
from ally.http.spec.server import RequestHTTP, ResponseHTTP, RequestContentHTTP, \
    ResponseContentHTTP
from ally.support.util_io import IInputStream, readGenerator
from urllib.parse import parse_qsl
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@injected
class RequestHandler:
    '''
    The server class that handles the requests.
    '''
    
    serverVersion = str
    # The server version name
    headerPrefix = 'HTTP_'
    # The prefix used in the WSGI context for the headers.
    headers = {'CONTENT_TYPE', 'CONTENT_LENGTH'}
    # The headers to be extracted from environment, this are the exception headers, the ones that do not start with HTTP_
    assembly = Assembly
    # The assembly used for resolving the requests

    def __init__(self):
        assert isinstance(self.serverVersion, str), 'Invalid server version %s' % self.serverVersion
        assert isinstance(self.headerPrefix, str), 'Invalid header prefix %s' % self.headerPrefix
        assert isinstance(self.headers, set), 'Invalid headers %s' % self.headers
        assert isinstance(self.responses, dict), 'Invalid responses %s' % self.responses
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        
        processing, report = self.assembly.create(ONLY_AVAILABLE, CREATE_REPORT,
                                                  request=RequestHTTP, requestCnt=RequestContentHTTP,
                                                  response=ResponseHTTP, responseCnt=ResponseContentHTTP)

        log.info('Assembly report for server:\n%s', report)
        self.processing = processing
        
        self.defaultHeaders = {'Server':self.serverVersion, 'Content-Type':'text'}

    def __call__(self, context, respond):
        '''
        Process the WSGI call.
        '''
        assert isinstance(context, dict), 'Invalid context %s' % context
        assert callable(respond), 'Invalid respond callable %s' % respond
        
        proc = self.processing
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        req, reqCnt = proc.contexts['request'](), proc.contexts['requestCnt']()
        rsp, rspCnt = proc.contexts['response'](), proc.contexts['responseCnt']()

        assert isinstance(req, RequestHTTP), 'Invalid request %s' % req
        assert isinstance(reqCnt, RequestContentHTTP), 'Invalid request content %s' % reqCnt
        assert isinstance(rsp, ResponseHTTP), 'Invalid response %s' % rsp
        assert isinstance(rspCnt, ResponseContentHTTP), 'Invalid response content %s' % rspCnt

        req.scheme, req.uri = context['wsgi.url_scheme'].upper(), context['PATH_INFO']
        if req.uri.startswith('/'): req.uri = req.uri[1:]

        responseHeaders = dict(self.defaultHeaders)

        req.method = context['REQUEST_METHOD']
        if req.method: req.method = req.method.upper()
        
        req.parameters = parse_qsl(context['QUERY_STRING'], True, False)
        prefix, prefixLen = self.headerPrefix, len(self.headerPrefix,)
        req.headers = {hname[prefixLen:].replace('_', '-'):hvalue
                       for hname, hvalue in context.items() if hname.startswith(prefix)}
        req.headers.update({hname.replace('_', '-'):hvalue
                            for hname, hvalue in context.items() if hname in self.headers})
        reqCnt.source = context.get('wsgi.input')

        Chain(proc).process(request=req, requestCnt=reqCnt, response=rsp, responseCnt=rspCnt).doAll()

        assert isinstance(rsp.status, int), 'Invalid response code status %s' % rsp.status

        responseHeaders.update(rsp.headers)
        if ResponseHTTP.text in rsp: status = '%s %s' % (rsp.status, rsp.text)
        else: status = str(rsp.status)

        respond(status, list(responseHeaders.items()))

        if rspCnt.source is not None:
            if isinstance(rspCnt.source, IInputStream): return readGenerator(rspCnt.source)
            return rspCnt.source
        return ()
