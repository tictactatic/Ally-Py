'''
Created on Feb 8, 2013

@package: gateway service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the forwarding processor.
'''

from ally.container.ioc import injected
from ally.design.context import Context, requires
from ally.design.processor import Assembly, ONLY_AVAILABLE, \
    NO_MISSING_VALIDATION, CREATE_REPORT, Processing, Chain, HandlerProcessor
from ally.gateway.http.spec.gateway import IRepository, Match, Gateway
from ally.http.spec.server import RequestHTTP, ResponseContentHTTP, \
    RequestContentHTTP, ResponseHTTP
from ally.support.util_io import IInputStream
from urllib.parse import urlparse, parse_qsl
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    Context for request. 
    '''
    # ---------------------------------------------------------------- Required
    scheme = requires(str)
    method = requires(str)
    headers = requires(dict)
    uri = requires(str)
    parameters = requires(list)
    match = requires(Match)

class RequestContent(Context):
    '''
    Context for request content. 
    '''
    # ---------------------------------------------------------------- Required
    source = requires(IInputStream)

# --------------------------------------------------------------------

@injected
class GatewayForwardHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the gateway forward.
    '''
    
    assembly = Assembly
    # The assembly to be used in processing the request for the filters.
    
    def __init__(self):
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__()

        processing, report = self.assembly.create(ONLY_AVAILABLE, NO_MISSING_VALIDATION, CREATE_REPORT,
                                                  request=RequestHTTP, requestCnt=RequestContentHTTP,
                                                  response=ResponseHTTP, responseCnt=ResponseContentHTTP)

        log.info('Assembly report for Forward:\n%s', report)
        self._processing = processing

    def process(self, chain, request:Request, requestCnt:RequestContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
        if Request.match not in request:
            # No forwarding if there is no match on response
            chain.proceed()
            return  
        
        assert isinstance(request.repository, IRepository), 'Invalid request repository %s' % request.repository
        match = request.match
        assert isinstance(match, Match), 'Invalid response match %s' % match
        assert isinstance(match.gateway, Gateway), 'Invalid gateway %s' % match.gateway
        
        proc = self._processing
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        req, reqCnt = proc.ctx.request(), proc.ctx.requestCnt()
        assert isinstance(req, RequestHTTP), 'Invalid request %s' % req
        assert isinstance(reqCnt, RequestContentHTTP), 'Invalid request content %s' % reqCnt

        req.scheme, req.method = request.scheme, request.method
        req.headers = request.headers
        
        if match.gateway.navigate:
            uri = match.gateway.navigate.replace('*', request.uri)
            try: uri = uri.format(None, *match.groupsURI)
            except IndexError:
                raise Exception('Invalid navigate URI \'%s\' for groups %s' % (match.gateway.navigate, match.groupsURI))
            url = urlparse(uri)
            req.uri = url.path.lstrip('/')
            req.parameters = []
            req.parameters.extend(parse_qsl(url.query, True, False))
            req.parameters.extend(request.parameters)
        else:
            req.uri = request.uri
            req.parameters = request.parameters
        
        reqCnt.source = requestCnt.source
        assert log.debug('Forwarding request to \'%s\'', req.uri) or True
        
        chain.update(request=req, requestCnt=reqCnt, response=proc.ctx.response(), responseCnt=proc.ctx.responseCnt())
        chain.branch(proc)
