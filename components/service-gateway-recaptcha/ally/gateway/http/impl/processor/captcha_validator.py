'''
Created on Jun 7, 2013

@package: gateway service reCAPTCHA
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the captcha validation.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranchingProceed
from ally.design.processor.processor import Using
from ally.gateway.http.impl.processor import respository
from ally.gateway.http.spec.gateway import IRepository
from ally.http.spec.codes import isSuccess, INVALID_AUTHORIZATION
from ally.http.spec.server import HTTP, RequestHTTP, RequestContentHTTP, \
    ResponseHTTP, ResponseContentHTTP, HTTP_POST, IDecoderHeader
from ally.support.util_io import IInputStream
from collections import Iterable
from io import BytesIO
from urllib.parse import quote_plus

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
    
class Request(respository.Request):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    method = requires(str)
    headers = requires(dict)
    uri = requires(str)
    clientIP = requires(str)
    match = requires(Context)
    decoderHeader = requires(IDecoderHeader)
# TODO: Gabriel
# class RequestContentVerify(RequestContentHTTP):
#    '''
#    The request content context.
#    '''
#    # ---------------------------------------------------------------- Defines
#    length = defines(int)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(str)
    status = defines(int)
    isSuccess = defines(bool)
    
class ResponseContent(RequestContentHTTP):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defines
    source = defines(Iterable)
    length = defines(int)
    
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
    message = 'privatekey=%(key)s&remoteip=%(clientIP)s&challenge=%(challenge)s&response=%(resolve)s'
    # The message to send for validation.
    nameChallenge = 'X-CAPTCHA-Challenge'
    # The header name for the reCAPTCHA challenge.
    nameResponse = 'X-CAPTCHA-Response'
    # The header name for the reCAPTCHA response.
    
    def __init__(self):
        assert isinstance(self.scheme, str), 'Invalid scheme %s' % self.scheme
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        assert isinstance(self.uriVerify, str), 'Invalid verify URI %s' % self.uriVerify
        assert isinstance(self.privateKey, str), 'Invalid private key %s' % self.privateKey
        assert isinstance(self.message, str), 'Invalid message %s' % self.message
        assert isinstance(self.nameChallenge, str), 'Invalid header name challenge %s' % self.nameChallenge
        assert isinstance(self.nameResponse, str), 'Invalid header name response %s' % self.nameResponse
        super().__init__(Using(self.assembly, request=RequestHTTP, requestCnt=RequestContentHTTP,
                               response=ResponseHTTP, responseCnt=ResponseContentHTTP))

    # TODO: Gabriel: Move Gateway, Match in __init__ after refactoring.
    def process(self, processing, request:Request, response:Response, responseCnt: ResponseContent,
                Gateway:Gateway, Match:Match, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Provides the gateway captcha validation.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        if not request.match: return
        assert isinstance(request.match, Match), 'Invalid match %s' % request.match
        if not request.match.gateway: return
        assert isinstance(request.match.gateway, Gateway), 'Invalid gateway %s' % request.match.gateway
        if not request.match.gateway.isWithCaptcha: return
        
        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid decoder header %s' % request.decoderHeader
        challenge = request.decoderHeader.retrieve(self.nameChallenge)
        resolve = request.decoderHeader.retrieve(self.nameResponse)
        
        if challenge and resolve:
            verified = self.checkCaptcha(processing, request.clientIP, challenge, resolve)
            if verified is not True:
                request.match = None
                responseCnt.source = (verified,)
                responseCnt.length = len(verified)
                response.code, response.status, response.isSuccess = INVALID_AUTHORIZATION
        else:
            if request.repository:
                assert isinstance(request.repository, IRepository), 'Invalid repository %s' % request.repository
                request.match = request.repository.find(request.method, request.headers, request.uri, INVALID_AUTHORIZATION.status)
            else: request.match = None
            response.code, response.status, response.isSuccess = INVALID_AUTHORIZATION
            
    # ----------------------------------------------------------------
    
    def checkCaptcha(self, processing, clientIP, challenge, resolve):
        '''
        Checks the filter URI.
        
        @param processing: Processing
            The processing used for delivering the request.
        @return: boolean
            True if the captcha is valid, False otherwise.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        
        request, requestCnt = processing.ctx.request(), processing.ctx.requestCnt()
        assert isinstance(request, RequestHTTP), 'Invalid request %s' % request
        assert isinstance(requestCnt, RequestContentHTTP), 'Invalid request content %s' % requestCnt
        
        request.scheme, request.method = self.scheme, HTTP_POST
        request.headers = {}
        request.uri = self.uriVerify
        request.parameters = []
        
        message = self.message % dict(key=quote_plus(self.privateKey, safe=''), clientIP=quote_plus(clientIP, safe=''), challenge=quote_plus(challenge, safe=''), resolve=quote_plus(resolve, safe=''))
        message = message.encode(encoding='ascii')
        requestCnt.source = (message,)
        request.headers['Content-Length'] = str(len(message))
        request.headers['Content-type'] = 'application/x-www-form-urlencoded'
        # TODO: It should be like after integration with refactored: requestCnt.length = len(requestCnt.source)
        
        chain = Chain(processing)
        chain.process(request=request, requestCnt=requestCnt,
                      response=processing.ctx.response(), responseCnt=processing.ctx.responseCnt()).doAll()

        response, responseCnt = chain.arg.response, chain.arg.responseCnt
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        
        if ResponseContentHTTP.source not in responseCnt or responseCnt.source is None or not isSuccess(response.status):
            return b'server-error'
        
        if isinstance(responseCnt.source, IInputStream):
            source = responseCnt.source
        else:
            source = BytesIO()
            for bytes in responseCnt.source: source.write(bytes)
            source.seek(0)
        content = source.read()
        if content.startswith(b'true'): return True
        return content
