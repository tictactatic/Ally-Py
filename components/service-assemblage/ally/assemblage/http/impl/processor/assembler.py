'''
Created on Mar 27, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assembler processor.
'''

from ally.assemblage.http.spec.assemblage import IRepository
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.branch import Using
from ally.design.processor.context import Context, pushIn
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranchingProceed
from ally.http.spec.server import IDecoderHeader
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    repository = requires(IRepository)
    decoderHeader = requires(IDecoderHeader)

# --------------------------------------------------------------------

@injected
class AssemblerHandler(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the assembling.
    '''
    
    nameAssemblage = 'X-Filter'
    # The header name for the assemblage request.
    assembly = Assembly
    # The assembly to be used in processing the request.
    
    def __init__(self):
        assert isinstance(self.nameAssemblage, str), 'Invalid assemblage name %s' % self.nameAssemblage
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Using(self.assembly, 'request', 'requestCnt', 'response', 'responseCnt'))

    def process(self, processing, request:Request, requestCnt:Context, response:Context, responseCnt:Context, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Assemble response content.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        
        #TODO: Gabriel: remove
        print(request.uri)
        rsp, rspCnt = self.obtainResponse(processing, request, requestCnt)
        pushIn(response, rsp)
        pushIn(responseCnt, rspCnt)
        
    # ----------------------------------------------------------------
   
    def obtainResponse(self, processing, request, requestCnt):
        '''
        Get the response for the request.
        
        @param processing: Processing
            The processing used for delivering the request.
        @param request: object
            The request object to deliver.
        @return: 
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        
        chain = Chain(processing)
        chain.process(request=request, requestCnt=requestCnt,
                      response=processing.ctx.response(), responseCnt=processing.ctx.responseCnt()).doAll()

        return chain.arg.response, chain.arg.responseCnt
