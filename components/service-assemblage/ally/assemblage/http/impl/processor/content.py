'''
Created on Apr 5, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content handler, this refers also to inner an main response content handling.
'''

from ally.assemblage.http.spec.assemblage import RequestNode
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.branch import Routing, Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranching
from ally.design.processor.spec import ContextMetaClass
from ally.http.spec.codes import isSuccess
from ally.http.spec.server import RequestHTTP, ResponseHTTP, HTTP_GET, \
    ResponseContentHTTP
from ally.support.util_io import StreamOnIterable, IInputStreamCT, IInputStream, \
    TellPosition
from collections import Callable
from functools import partial
from urllib.parse import urlsplit, parse_qsl
import codecs
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

UNAVAILABLE = 417, 'Unavailable content'  # HTTP code 417 Expectation Failed

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    scheme = requires(str)
    headers = requires(dict)
    # ---------------------------------------------------------------- Defined
    parameters = defines(list)
    
class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Defined
    main = defines(object, doc='''
    @rtype: Content
    The main response content.
    ''')
    requestHandler = defines(Callable, doc='''
    @rtype: callable(string, list[tuple(string, string)]) -> Content
    The request handler that takes as arguments the URL and parameters to process the request and returns the content.
    ''')
    # ---------------------------------------------------------------- Optional
    ecodingError = optional(str, doc='''
    @rtype: string
    The character set encoding error.
    ''')
    decode = defines(Callable, doc='''
    @rtype: callable(bytes) -> string
    The decoder that converts from the response encoding bytes to string.
    ''')
    # ---------------------------------------------------------------- Required
    requestNode = requires(RequestNode)

class ContentResponse(Context):
    '''
    The assemblage content context.
    '''
    # ---------------------------------------------------------------- Defined
    errorStatus = defines(int, doc='''
    @rtype: integer
    The error status obtained when fetching the content.
    ''')
    errorText = defines(str, doc='''
    @rtype: string
    The error text obtained when fetching the content.
    ''')
    source = defines(IInputStreamCT, doc='''
    @rtype: IInputStreamCT
    The content input stream source.
    ''')
    encode = defines(Callable, doc='''
    @rtype: callable(bytes|string) -> bytes
    The encoder that converts from the source encoding or an arbitrary string to the expected response encoding.
    ''')
    # ---------------------------------------------------------------- Required
    charSet = requires(str)
    
# --------------------------------------------------------------------

@injected
class ContentHandler(HandlerBranching):
    '''
    Makes the main request that assemblage will be constructed on. If the response is not suited for assemblage this
    handler will stop the chain and provide as a response the error response.
    '''
    
    assemblyForward = Assembly
    # The assembly to be used in forwarding the request.
    assemblyContent = Assembly
    # The assembly to be used in handling the content.
    encodingError = 'replace'
    # The encoding error resolving if none provided.
    
    def __init__(self):
        assert isinstance(self.assemblyForward, Assembly), 'Invalid request forward assembly %s' % self.assemblyForward
        assert isinstance(self.assemblyContent, Assembly), 'Invalid content assembly %s' % self.assemblyContent
        assert isinstance(self.encodingError, str), 'Invalid encoding error %s' % self.encodingError
        super().__init__(Routing(self.assemblyForward).using('request', 'requestCnt', 'response', 'responseCnt'),
                         Branch(self.assemblyContent).included('response', 'assemblage', ('content', 'Content')))

    def process(self, chain, processingForward, processingContent, request:Request, requestCnt:Context, response:Context,
                responseCnt:Context, assemblage:Assemblage, Content:ContentResponse, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Provide the content handling.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processingForward, Processing), 'Invalid processing %s' % processingForward
        assert isinstance(processingContent, Processing), 'Invalid processing %s' % processingContent
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        assert issubclass(Content, ContentResponse), 'Invalid content class %s' % Content
        
        if assemblage.requestNode:
            assert isinstance(assemblage.requestNode, RequestNode), 'Invalid request node %s' % assemblage.requestNode
            request.parameters = assemblage.requestNode.parameters
            
            data = Data()
            data.assemblage = assemblage
            data.processingForward, data.processingContent = processingForward, processingContent
            data.Request, data.RequestContent = request.__class__, requestCnt.__class__
            data.Response, data.ResponseContent = response.__class__, responseCnt.__class__
            data.Content = Content
            data.scheme, data.headers = request.scheme, dict(request.headers)
        
        chainForward = Chain(processingForward)
        chainForward.process(request=request, requestCnt=requestCnt, response=response, responseCnt=responseCnt).doAll()
        response, responseCnt = chainForward.arg.response, chainForward.arg.responseCnt
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        chain.update(response=response, responseCnt=responseCnt)
        
        chainContent = Chain(processingContent)
        chainContent.process(response=response, assemblage=assemblage, content=Content()).doAll()
        content = chainContent.arg.content
        assert isinstance(content, ContentResponse), 'Invalid content %s' % content
        
        if not isSuccess(response.status):
            assert log.debug('Failed %s with %s', request, response) or True
            return
        if ResponseContentHTTP.source not in responseCnt or responseCnt.source is None:
            assert log.debug('No response content source for %s', request) or True
            return
        if assemblage.requestNode is None:
            assert log.debug('No request node available for %s', request) or True
            return
        if content.charSet is None:
            assert log.debug('No response content character set encoding for %s', request) or True
            return

        data.charSet = codecs.lookup(content.charSet).name
        assemblage.decode = partial(str, encoding=data.charSet)
        
        assemblage.main = self.populate(data, content, response, responseCnt)
        assemblage.requestHandler = partial(self.handler, data)
        
        chain.proceed()
        
    # --------------------------------------------------------------------
    
    def populate(self, data, content, response, responseCnt):
        '''
        Populates the content object based on the response and response content.
        
        @param data: Data
            The data to use for content populating.
        @param content: ContentResponse
            The content to populate.
        @param response: ResponseHTTP
            The response to populate the content based on.
        @param responseCnt: ResponseContent
            The response content to populate the content based on.
        @return: ContentResponse
            The populated content.
        '''
        assert isinstance(content, ContentResponse), 'Invalid content %s' % content
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        
        if not isSuccess(response.status):
            content.errorStatus = response.status
            if ResponseHTTP.text in response and response.text: content.errorText = response.text
            elif ResponseHTTP.code in response and response.code: content.errorText = response.code
            return content
            
        if ResponseContentHTTP.source not in responseCnt or responseCnt.source is None:
            content.errorStatus, content.errorText = UNAVAILABLE
            return content
        
        if isinstance(responseCnt.source, IInputStream): source = responseCnt.source
        else: source = StreamOnIterable(responseCnt.source)
        content.source = TellPosition(source)
        
        if content.charSet: content.encode = partial(self.encode, data, codecs.lookup(content.charSet).name)
        
        return content
            
    def encode(self, data, charSet, content):
        '''
        Encoder the provided bytes.
        
        @param data: Data
            The data to use for encode.
        @param charSet: string
            The character set that the bytes are encoded in.
        @param content: bytes|string
            The bytes to encode.
        @return: bytes
            The encoded bytes.
        '''
        assert isinstance(data, Data), 'Invalid data %s' % data
        assert isinstance(data.assemblage, Assemblage), 'Invalid assemblage %s' % data.assemblage
        assert isinstance(data.charSet, str), 'Invalid assemblage character set %s' % data.charSet
        assert isinstance(charSet, str), 'Invalid character set %s' % charSet
        
        if Assemblage.ecodingError in data.assemblage and data.assemblage.ecodingError:
            error = data.assemblage.ecodingError
        else: error = self.encodingError
        
        if isinstance(content, str): return content.encode(data.charSet, error)
        else:
            if data.charSet == charSet: return content
            return str(content, charSet).encode(data.charSet, error)
    
    def handler(self, data, url, parameters=None):
        '''
        Handles the requests.
        
        @param data: Data
            The data to use for dispatching the request.
        @param url: string
            The requested URL.
        @param parameters: list[tuple(string, string)]|None
            The list of parameters for the request.
        '''
        assert isinstance(data, Data), 'Invalid data %s' % data
        assert isinstance(data.Content, ContextMetaClass), 'Invalid content class %s' % data.Content
        assert isinstance(data.assemblage, Assemblage), 'Invalid assemblage %s' % data.assemblage
        assert isinstance(url, str), 'Invalid URL %s' % url
        assert parameters is None or isinstance(parameters, list), 'Invalid parameters %s' % parameters
        
        request = data.Request()
        assert isinstance(request, RequestHTTP), 'Invalid request %s' % request
        
        rurl = urlsplit(url)
        
        params = parse_qsl(rurl.query, True, False)
        if parameters: params.extend(parameters)
        
        request.scheme = data.scheme
        request.method = HTTP_GET
        request.headers = dict(data.headers)
        request.uri = rurl.path.lstrip('/')
        request.parameters = params
        
        proc = data.processingForward
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        chainForward = Chain(proc)
        keyargs = proc.fillIn(request=request, requestCnt=data.RequestContent(), response=data.Response(),
                              responseCnt=data.ResponseContent())
        chainForward.process(**keyargs).doAll()
        
        proc = data.processingContent
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        chainContent = Chain(proc)
        keyargs = proc.fillIn(response=chainForward.arg.response, assemblage=data.assemblage, content=data.Content())
        chainContent.process(**keyargs).doAll()
                
        return self.populate(data, chainContent.arg.content, chainForward.arg.response, chainForward.arg.responseCnt)

# --------------------------------------------------------------------

class Data:
    '''
    The data container used in processing.
    '''
    __slots__ = ('assemblage', 'processingForward', 'processingContent', 'Response', 'ResponseContent', 'Request',
                 'RequestContent', 'Content', 'scheme', 'headers', 'charSet')
    if False:
        # Just for auto complete.
        assemblage = Assemblage  # The assemblage containing data to use for content populating.
        processingForward = Processing  # The processing used for solving the request.
        processingContent = Processing  # The assembly to be used in handling the content.
        Response = ContextMetaClass  # The response context.
        ResponseContent = ContextMetaClass  # The response content context.
        Request = ContextMetaClass  # The request context.
        RequestContent = ContextMetaClass  # The request content context.
        Content = ContextMetaClass  # The content context class used in constructing the returned objects.
        scheme = str  # The scheme used for inner requests.
        headers = dict  # The headers to be used for inner requests.
        charSet = str  # The character set that the response need to be encoded in.
