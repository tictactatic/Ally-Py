'''
Created on Mar 27, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assembler processor.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Using
from ally.design.processor.context import Context, pushIn
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranchingProceed
from ally.http.spec.codes import isSuccess
from ally.http.spec.server import ResponseHTTP, RequestHTTP, RequestContentHTTP
from ally.support.util_io import IInputStream
from codecs import getreader, getwriter
from collections import Iterable
from io import BytesIO
import logging
import json
from ally.assemblage.http.spec.assemblage import RequestNode

# --------------------------------------------------------------------

UNKNOWN_ENCODING = 417, 'Unknown encoding'  # HTTP code 417 Expectation Failed
UNAVAILABLE_INDEX = 417, 'Unavailable indexes'  # HTTP code 417 Expectation Failed

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    scheme = requires(str)
    headers = requires(dict)
    requestNode = requires(RequestNode)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    source = requires(IInputStream, Iterable)
    charSet = requires(str)
    indexes = requires(list)
    
class RequestInner(Context):
    '''
    The request inner context.
    '''
    # ---------------------------------------------------------------- Defined
    scheme = defines(str)
    method = defines(str)
    headers = defines(dict)
    uri = defines(str)
    headers = defines(dict)
    parameters = defines(list)

class RequestContentInner(Context):
    '''
    The request inner content context.
    '''
    # ---------------------------------------------------------------- Defined
    source = defines(IInputStream)

# --------------------------------------------------------------------

@injected
class AssemblerHandler(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the assembling.
    '''
    
    assembly = Assembly
    # The assembly to be used in processing the inner requests.
    
    def __init__(self):
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Using(self.assembly, request=RequestInner, requestCnt=RequestContentInner,
                               response=ResponseHTTP, responseCnt=ResponseContent))

    def process(self, processing, request:Request, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Assemble response content.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        
        
    # ----------------------------------------------------------------
    
#    def fetchResponse(self, processing, request, requestCnt=None):
#        '''
#        Fetch the response for the request.
#        
#        @param processing: Processing
#            The processing used for delivering the request.
#        @param request: RequestHTTP
#            The request object to deliver.
#        @return: tuple(boolean, ResponseHTTP, ResponseContentHTTP)
#            A tuple of three containing a flag indicating the success status and then the response and response content.
#        '''
#        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
#        
#        if requestCnt is None: requestCnt = processing.ctx.requestCnt()
#        chain = Chain(processing)
#        chain.process(request=request, requestCnt=requestCnt,
#                      response=processing.ctx.response(), responseCnt=processing.ctx.responseCnt()).doAll()
#    
#        response, responseCnt = chain.arg.response, chain.arg.responseCnt
#        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
#        assert isinstance(responseCnt, ResponseContentData), 'Invalid response content %s' % responseCnt
#        
#        isOk = ResponseContentData.source in responseCnt and responseCnt.source is not None and isSuccess(response.status)
#        return isOk, response, responseCnt
#    
#    def fetchContent(self, responseCnt):
#        '''
#        Fetches the text content into a string, None if the content type is no usable.
#        
#        @param responseCnt: ResponseContentData
#            The response content to fetch the content from.
#        @param maximum: integer|None
#            The maximum allowed length for the response in order to be fetched.
#        @return: tuple(tuple(integer, string|None), string|None)
#            A tuple of two, on the first position the error explanation if there was a problem, the error is
#            provided as a tuple having on the first position the HTTP status code and on the second text explanation, and
#            on the second position the content string or None if a problem occurred.
#        '''
#        assert isinstance(responseCnt, ResponseContentData), 'Invalid response content %s' % responseCnt
#        
#        try: decoder = getreader(responseCnt.charSet)
#        except LookupError: return UNKNOWN_ENCODING, None
#        
#        if isinstance(responseCnt.source, IInputStream):
#            source = responseCnt.source
#        else:
#            source = BytesIO()
#            for bytes in responseCnt.source: source.write(bytes)
#            source.seek(0)
#        
#        return None, decoder(source).read()
