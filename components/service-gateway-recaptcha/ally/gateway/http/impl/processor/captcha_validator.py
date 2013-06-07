'''
Created on Jun 7, 2013

@package: gateway service reCAPTCHA
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the captcha validation.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerBranchingProceed
from ally.design.processor.assembly import Assembly
from ally.http.spec.server import HTTP, RequestHTTP, RequestContentHTTP, \
    ResponseHTTP, ResponseContentHTTP, HTTP_POST
from ally.design.processor.processor import Using
from ally.design.processor.execution import Processing, Chain
from ally.http.spec.codes import isSuccess
from ally.support.util_io import IInputStream
from io import BytesIO

# --------------------------------------------------------------------

class Gateway(Context):
    '''
    The gateway context.
    '''
    # ---------------------------------------------------------------- Required
    isWithCaptcha = requires(bool)

class Match(Context):
    '''
    The match context.
    '''
    # ---------------------------------------------------------------- Required
    gateway = requires(Context)
    
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    match = requires(Context)
    
# --------------------------------------------------------------------

@injected
class GatewayCaptchaValidationHandler(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the gateway captcha validation.
    '''
    
    scheme = HTTP
    # The scheme to be used in calling the reCAPTCHA service.
    assembly = Assembly
    # The assembly to be used in processing the reCAPTCHA request for validation
    uriVerify = str
    # The reCAPTCHA service URI used for verifying the captcha.
    privateKey = str
    # The reCAPTCHA private key to use.
    
    def __init__(self):
        assert isinstance(self.scheme, str), 'Invalid scheme %s' % self.scheme
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        assert isinstance(self.uriVerify, str), 'Invalid verify URI %s' % self.uriVerify
        assert isinstance(self.privateKey, str), 'Invalid private key %s' % self.privateKey
        super().__init__(Using(self.assembly, request=RequestHTTP, requestCnt=RequestContentHTTP,
                               response=ResponseHTTP, responseCnt=ResponseContentHTTP))

    # TODO: Gabriel: Move Gateway, Match in __init__ after refactoring.
    def process(self, processing, request:Request, Gateway:Gateway, Match:Match, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Provides the gateway captcha validation.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        if not request.match: return
        assert isinstance(request.match, Match), 'Invalid match %s' % request.match
        if not request.match.gateway: return
        assert isinstance(request.match.gateway, Gateway), 'Invalid gateway %s' % request.match.gateway
        if not request.match.gateway.isWithCaptcha: return

        #TODO: continue
        self.checkCaptcha(processing)
        
    # ----------------------------------------------------------------
    
    def checkCaptcha(self, processing):
        '''
        Checks the filter URI.
        
        @param processing: Processing
            The processing used for delivering the request.
        @return: boolean
            True if the captcha is valid, False otherwise.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        
        request = processing.ctx.request()
        assert isinstance(request, RequestHTTP), 'Invalid request %s' % request
        
        request.scheme, request.method = self.scheme, HTTP_POST
        request.headers = {}
        request.uri = self.uriVerify
        request.parameters = []
        
        chain = Chain(processing)
        chain.process(request=request, requestCnt=processing.ctx.requestCnt(),
                      response=processing.ctx.response(), responseCnt=processing.ctx.responseCnt()).doAll()

        response, responseCnt = chain.arg.response, chain.arg.responseCnt
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        
        if ResponseHTTP.text in response and response.text: text = response.text
        elif ResponseHTTP.code in response and response.code: text = response.code
        else: text = None
        
#        if ResponseContentHTTP.source not in responseCnt or responseCnt.source is None or not isSuccess(response.status):
#            return None, response.status, text
        
        if isinstance(responseCnt.source, IInputStream):
            source = responseCnt.source
        else:
            source = BytesIO()
            for bytes in responseCnt.source: source.write(bytes)
            source.seek(0)
        print(source.read())
