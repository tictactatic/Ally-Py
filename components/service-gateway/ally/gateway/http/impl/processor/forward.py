'''
Created on Feb 8, 2013

@package: gateway service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the forwarding processor.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.branch import Branch
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranching
from ally.gateway.http.spec.gateway import IRepository, Match, Gateway
from ally.http.spec.headers import HeadersRequire
from urllib.parse import urlparse, parse_qsl
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(HeadersRequire):
    '''
    Context for request. 
    '''
    # ---------------------------------------------------------------- Required
    uri = requires(str)
    parameters = requires(list)
    match = requires(Match)

# --------------------------------------------------------------------

@injected
class GatewayForwardHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the gateway forward.
    '''
    
    assembly = Assembly
    # The assembly to be used in processing the request.
    
    def __init__(self):
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Branch(self.assembly).included())

    def process(self, chain, processing, request:Request, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Process the forward.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        
        if not request.match: return  # No forwarding if there is no match on response
        
        assert isinstance(request.repository, IRepository), 'Invalid request repository %s' % request.repository
        match = request.match
        assert isinstance(match, Match), 'Invalid response match %s' % match
        assert isinstance(match.gateway, Gateway), 'Invalid gateway %s' % match.gateway
        
        if match.gateway.navigate:
            uri = match.gateway.navigate.replace('*', request.uri)
            try: uri = uri.format(None, *match.groupsURI)
            except IndexError:
                raise Exception('Invalid navigate URI \'%s\' for groups %s' % (match.gateway.navigate, match.groupsURI))
            url = urlparse(uri)
            request.uri = url.path.lstrip('/')
            parameters = parse_qsl(url.query, True, False)
            if request.parameters: parameters.extend(request.parameters)
            request.parameters = parameters
        
        if match.gateway.putHeaders:
            nheaders = {}
            if request.headers is not None: remove = set()
            for name, value in match.gateway.putHeaders:
                nheaders[name] = value
                if request.headers:
                    assert isinstance(request.headers, dict), 'Invalid headers %s' % request.headers
                    for hname in request.headers:
                        if hname.lower() == name: remove.add(hname)
                
            if request.headers is None: request.headers = nheaders
            else:
                for hname in remove: request.headers.pop(hname)
                request.headers.update(nheaders)
        
        assert log.debug('Forwarding request to \'%s\'', request.uri) or True
        # TODO: Gabriel, this is a temporary fix, we need to provide a handler that properly handles the response and response content
        # isolation.
        nresponse = chain.arg.response.__class__()
        nresponseCnt = chain.arg.responseCnt.__class__()
        chain.update(response=nresponse, responseCnt=nresponseCnt)
        chain.branch(processing)
