'''
Created on Feb 8, 2013

@package: gateway service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the gateway filter processor.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.gateway.http.spec.gateway import IRepository
from ally.http.spec.codes import FORBIDDEN_ACCESS, BAD_GATEWAY, CodedHTTP
from ally.http.spec.headers import HeadersRequire
from ally.support.http.util_dispatch import RequestDispatch, obtainJSON
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Gateway(Context):
    '''
    The gateway context.
    '''
    # ---------------------------------------------------------------- Required
    filters = requires(list)
    
class Match(Context):
    '''
    The match context.
    '''
    # ---------------------------------------------------------------- Required
    gateway = requires(Context)
    groupsURI = requires(tuple)
    
class Request(HeadersRequire):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    method = requires(str)
    uri = requires(str)
    repository = requires(IRepository)
    match = requires(Context)
    
class Response(CodedHTTP):
    '''
    Context for response. 
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)

# --------------------------------------------------------------------

@injected
class GatewayFilterHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the gateway filter.
    '''
    
    assembly = Assembly
    # The assembly to be used in processing the request for the filters.
    
    def __init__(self):
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Branch(self.assembly).using('requestCnt', 'response', 'responseCnt', request=RequestDispatch),
                         Gateway=Gateway, Match=Match)

    def process(self, chain, processing, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerBranching.process
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if not request.match: return  # No filtering is required if there is no match on request
        
        assert isinstance(request.repository, IRepository), 'Invalid request repository %s' % request.repository
        match = request.match
        assert isinstance(match, Match), 'Invalid response match %s' % match
        assert isinstance(match.gateway, Gateway), 'Invalid gateway %s' % match.gateway
        
        if match.gateway.filters:
            for filterURI in match.gateway.filters:
                assert isinstance(filterURI, str), 'Invalid filter %s' % filterURI
                try: filterURI = filterURI.format(None, *match.groupsURI)
                except IndexError:
                    BAD_GATEWAY.set(response)
                    response.text = 'Invalid filter URI \'%s\' for groups %s' % (filterURI, match.groupsURI)
                    return
                
                jobj, status, text = obtainJSON(processing, filterURI, details=True)
                if jobj is None:
                    log.error('Cannot fetch the filter from URI \'%s\', with response %s %s', request.uri, status, text)
                    BAD_GATEWAY.set(response)
                    response.text = text
                    return
                
                if jobj['HasAccess'] != True:
                    FORBIDDEN_ACCESS.set(response)
                    request.match = request.repository.find(request.method, request.headers, request.uri,
                                                            FORBIDDEN_ACCESS.status)
                    return
