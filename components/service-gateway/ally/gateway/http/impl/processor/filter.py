'''
Created on Feb 8, 2013

@package: gateway service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the gateway filter processor.
'''

from ally.container.ioc import injected
from ally.design.context import Context, requires, defines
from ally.design.processor import HandlerProcessorProceed, Assembly, \
    ONLY_AVAILABLE, NO_MISSING_VALIDATION, CREATE_REPORT, Processing, Chain
from ally.gateway.http.spec.gateway import IRepository, Match, Gateway
from ally.http.spec.server import HTTP, RequestHTTP, ResponseContentHTTP, \
    RequestContentHTTP, ResponseHTTP, HTTP_GET
from ally.support.util_io import IInputStream
from babel.compat import BytesIO
from urllib.parse import urlparse, parse_qsl
import codecs
import json
import logging
from ally.http.spec.codes import FORBIDDEN_ACCESS

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    method = requires(str)
    headers = requires(dict)
    uri = requires(str)
    repository = requires(IRepository)
    match = requires(Match)
    
class Response(Context):
    '''
    Context for response. 
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(str)
    status = defines(int)
    isSuccess = defines(bool)
    
class RequestFilter(RequestHTTP):
    '''
    The request filter context.
    '''
    # ---------------------------------------------------------------- Defined
    type = defines(str)

class ResponseContentFilter(ResponseContentHTTP):
    '''
    The response filter content context.
    '''
    # ---------------------------------------------------------------- Required
    charSet = requires(str)

# --------------------------------------------------------------------

@injected
class GatewayFilterHandler(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the gateway filter.
    '''
    
    scheme = HTTP
    # The scheme to be used in calling the filters.
    mimeTypeJson = 'json'
    # The json mime type to be sent for the filter requests.
    assembly = Assembly
    # The assembly to be used in processing the request for the filters.
    
    def __init__(self):
        assert isinstance(self.scheme, str), 'Invalid scheme %s' % self.scheme
        assert isinstance(self.mimeTypeJson, str), 'Invalid json mime type %s' % self.mimeTypeJson
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__()

        processing, report = self.assembly.create(ONLY_AVAILABLE, NO_MISSING_VALIDATION, CREATE_REPORT,
                                                  request=RequestFilter, requestCnt=RequestContentHTTP,
                                                  response=ResponseHTTP, responseCnt=ResponseContentFilter)

        log.info('Assembly report for Filter:\n%s', report)
        self._processing = processing

    def process(self, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if Request.match not in request: return  # No filtering is required if there is no match on request
        
        assert isinstance(request.repository, IRepository), 'Invalid request repository %s' % request.repository
        match = request.match
        assert isinstance(match, Match), 'Invalid response match %s' % match
        assert isinstance(match.gateway, Gateway), 'Invalid gateway %s' % match.gateway
        
        cache = request.repository.obtainCache('filters')
        assert isinstance(cache, dict), 'Invalid cache %s' % cache
        if match.gateway.filters:
            for filterURI in match.gateway.filters:
                assert isinstance(filterURI, str), 'Invalid filter %s' % filterURI
                try: filterURI = filterURI.format(None, *match.groupsURI)
                except IndexError: raise Exception('Invalid filter URI \'%s\' for groups %s' % (filterURI, match.groupsURI))
                
                isAllowed = cache.get(filterURI)
                if isAllowed is None: isAllowed = cache[filterURI] = self.checkFilter(filterURI)
                
                if not isAllowed:
                    response.code, response.status, response.isSuccess = FORBIDDEN_ACCESS
                    request.match = request.repository.find(request.method, request.headers, request.uri, FORBIDDEN_ACCESS.status)
                    return
                
    # ----------------------------------------------------------------
    
    def checkFilter(self, uri):
        '''
        Checks the filter URI.
        
        @param uri: string
            The URI to call, parameters are allowed.
        @return: boolean
            True if the filter URI provided a True value, False otherwise.
        '''
        assert isinstance(uri, str), 'Invalid URI %s' % uri
        proc = self._processing
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        request = proc.ctx.request()
        assert isinstance(request, RequestFilter), 'Invalid request %s' % request
        
        url = urlparse(uri)
        request.scheme, request.method = self.scheme, HTTP_GET
        request.headers = {}
        request.uri = url.path.lstrip('/')
        request.parameters = parse_qsl(url.query, True, False)
        request.type = self.mimeTypeJson
        
        chain = Chain(proc)
        chain.process(request=request, requestCnt=proc.ctx.requestCnt()).doAll()

        response, responseCnt = chain.arg.response, chain.arg.responseCnt
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentFilter), 'Invalid response content %s' % responseCnt
        assert responseCnt.source is not None, 'Cannot fetch the gateways content from URI \'%s\', has a response %s %s' % \
        (uri, response.status, response.text or response.code)
        assert responseCnt.charSet, 'No character set available for response %s %s' % \
        (uri, response.status, response.text or response.code)
        
        if isinstance(responseCnt.source, IInputStream):
            source = responseCnt.source
        else:
            source = BytesIO()
            for bytes in responseCnt.source: source.write(bytes)
            source.seek(0)
        allowed = json.load(codecs.getreader(responseCnt.charSet)(source))
        return allowed['HasAccess'] == 'True'
