'''
Created on Feb 8, 2013

@package: gateway service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the gateway filter processor.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.gateway.http.spec.gateway import IRepository
from ally.http.spec.codes import FORBIDDEN_ACCESS, BAD_GATEWAY, CodedHTTP
from ally.http.spec.headers import HeadersRequire
import logging
from ally.support.http.request import RequesterGetJSON

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Gateway(Context):
    '''
    The gateway context.
    '''
    # ---------------------------------------------------------------- Required
    filters = requires(dict)

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
class GatewayFilterHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the gateway filter.
    '''

    requesterGetJSON = RequesterGetJSON
    # The requester for getting the filters.

    def __init__(self):
        assert isinstance(self.requesterGetJSON, RequesterGetJSON), 'Invalid requester JSON %s' % self.requesterGetJSON
        super().__init__(Gateway=Gateway, Match=Match)

    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if not request.match: return  # No filtering is required if there is no match on request

        assert isinstance(request.repository, IRepository), 'Invalid request repository %s' % request.repository
        match = request.match
        assert isinstance(match, Match), 'Invalid response match %s' % match
        assert isinstance(match.gateway, Gateway), 'Invalid gateway %s' % match.gateway

        if match.gateway.filters:
            for group, paths in match.gateway.filters.items():
                assert isinstance(paths, list), 'Invalid filter paths %s' % paths

                if group > len(match.groupsURI):
                    BAD_GATEWAY.set(response)
                    response.text = 'Invalid filter group \'%s\' for %s' % (group, match.groupsURI)
                    return

                for path in paths:
                    assert isinstance(path, str), 'Invalid path %s' % path
                    
                    path = path.replace('*', match.groupsURI[group - 1])
                    jobj, error = self.requesterGetJSON.request(path, details=True)
                    if jobj is None:
                        BAD_GATEWAY.set(response)
                        response.text = error.text
                        return
                    
                    if jobj['IsAllowed'] == True: break
                    
                else:
                    FORBIDDEN_ACCESS.set(response)
                    request.match = request.repository.find(request.method, request.headers, request.uri, FORBIDDEN_ACCESS.status)
                    return
