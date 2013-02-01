'''
Created on Jan 30, 2013

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides a processor that routes the requests based on patterns.
'''

from ally.container.ioc import injected
from ally.design.context import Context, requires, copy, defines
from ally.design.processor import Assembly, ONLY_AVAILABLE, CREATE_REPORT, Chain, \
    Processing, HandlerProcessor
from ally.http.spec.server import RequestHTTP, ResponseHTTP, RequestContentHTTP, \
    ResponseContentHTTP
from ally.support.util_io import IInputStream
from collections import Iterable
import logging
import re

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    Context for request data. 
    '''
    # ---------------------------------------------------------------- Required
    scheme = requires(str)
    method = requires(str)
    uri = requires(str)
    parameters = requires(list)
    headers = requires(dict)

class RequestContent(Context):
    '''
    Context for request content data. 
    '''
    # ---------------------------------------------------------------- Required
    source = requires(IInputStream)

class Response(Context):
    '''
    Context for response data. 
    '''
    # ---------------------------------------------------------------- Required
    status = defines(int)

class ResponseContent(Context):
    '''
    Context for response content data. 
    '''
    # ---------------------------------------------------------------- Defined
    source = defines(IInputStream, Iterable)

# --------------------------------------------------------------------

@injected
class RoutingByPathHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the routing of requests based on regex patterns. The regex needs to provide
    capturing groups that joined will become the routed uri. 
    '''
    
    pattern = str
    # The string pattern for matching the path, the pattern needs to provide capturing groups that joined will become
    # the routed uri. 
    assembly = Assembly
    # The assembly to be used in processing the request for the provided pattern.
    
    def __init__(self):
        assert isinstance(self.pattern, str), 'Invalid pattern %s' % self.pattern
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__()

        processing, report = self.assembly.create(ONLY_AVAILABLE, CREATE_REPORT,
                                                  request=RequestHTTP, requestCnt=RequestContentHTTP,
                                                  response=ResponseHTTP, responseCnt=ResponseContentHTTP)

        log.info('Assembly report for \'%s\':\n%s', re.sub('[\\/]+', '/', re.sub('([^\w\\/]*)', '', self.pattern)), report)
        self._regex = re.compile(self.pattern)
        self._processing = processing
            
    def process(self, chain, request:Request, requestCnt:RequestContent,
                response:Response=None, responseCnt:ResponseContent=None):
        '''
        Process the routing.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
        
        match = self._regex.match(request.uri)
        if match:
            proc = self._processing
            assert isinstance(proc, Processing), 'Invalid processing %s' % proc
            requestHTTP, requestCntHTTP = proc.ctx.request(), proc.ctx.requestCnt()
            responseHTTP, responseCntHTTP = proc.ctx.response(), proc.ctx.responseCnt()
            
            copy(request, requestHTTP)
            copy(requestCnt, requestCntHTTP)
            
            requestHTTP.uri = ''.join(match.groups())
            
            chain.update(request=requestHTTP, requestCnt=requestCntHTTP, response=responseHTTP, responseCnt=responseCntHTTP)
            chain.branch(self._processing)
        else:
            chain.proceed()
