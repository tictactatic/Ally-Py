'''
Created on Apr 5, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the main request handler.
'''

from ally.assemblage.http.spec.assemblage import RequestNode
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Included
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranching
from ally.http.spec.codes import isSuccess
from ally.support.util_io import IInputStream
from collections import Iterable

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    parameters = defines(list)
    # ---------------------------------------------------------------- Required
    requestNode = requires(RequestNode)
    
class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    status = requires(int)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    source = requires(IInputStream, Iterable)
    
# --------------------------------------------------------------------

@injected
class MainRequestHandler(HandlerBranching):
    '''
    Makes the main request that assemblage will be constructed on. If the response is not suited for assemblage this
    handler will stop the chain.
    '''
    
    assembly = Assembly
    # The assembly to be used in processing the request.
    
    def __init__(self):
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Included(self.assembly), response=Response, responseCnt=ResponseContent)

    def process(self, chain, processing, request:Request, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Provide the handling of the main request.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        
        if request.requestNode:
            assert isinstance(request.requestNode, RequestNode), 'Invalid request node %s' % request.requestNode
            request.parameters = request.requestNode.parameters
        
        chainMain = Chain(processing)
        chainMain.process(request=request, **keyargs).doAll()
    
        response, responseCnt = chainMain.arg.response, chainMain.arg.responseCnt
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        chain.update(response=response, responseCnt=responseCnt)
        
        if request.requestNode is None: return  # There is no assemblage request to proceed on.
        if not isSuccess(response.status): return  # Failed request, nothing to do.
        if responseCnt.source is None: return  # No content nothing to do.
        
        chain.proceed()
