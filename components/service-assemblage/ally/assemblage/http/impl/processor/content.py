'''
Created on Apr 5, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content handler, this refers also to inner an main response content handling.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Routing, Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing, Execution
from ally.design.processor.handler import HandlerBranching
from ally.design.processor.spec import ContextMetaClass
from ally.http.spec.codes import isSuccess
from ally.http.spec.headers import remove
from ally.http.spec.server import RequestHTTP, ResponseHTTP, HTTP_GET, \
    ResponseContentHTTP
from ally.support.util_io import StreamOnIterable, IInputStream
from ally.support.util_spec import IDo
from collections import Iterable
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
    clientIP = requires(str)
    scheme = requires(str)
    headers = requires(dict)
    
class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Defined
    main = defines(object, doc='''
    @rtype: Content
    The main response content.
    ''')
    doRequest = defines(IDo, doc='''
    @rtype: callable(string, list[tuple(string, string)]) -> Content
    The request handler that takes as arguments the URL and parameters to process the request and returns the content.
    ''')

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
    source = defines(IInputStream, doc='''
    @rtype: IInputStream
    The content input stream source.
    ''')
    doDecode = defines(IDo, doc='''
    @rtype: callable(bytes) -> string
    The decoder that converts from the response encoding bytes to string.
    ''')
    doEncode = defines(IDo, doc='''
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
    charSetDefault = str
    # The default character set to be used if none provided for the content.
    encodingError = 'replace'
    # The encoding error resolving if none provided.
    innerHeadersRemove = list
    # The headers to be removed from the inner requests.
    
    def __init__(self):
        assert isinstance(self.assemblyForward, Assembly), 'Invalid request forward assembly %s' % self.assemblyForward
        assert isinstance(self.assemblyContent, Assembly), 'Invalid content assembly %s' % self.assemblyContent
        assert isinstance(self.charSetDefault, str), 'Invalid default character set %s' % self.charSetDefault
        assert isinstance(self.encodingError, str), 'Invalid encoding error %s' % self.encodingError
        assert isinstance(self.innerHeadersRemove, list), 'Invalid inner headers remove %s' % self.innerHeadersRemove
        super().__init__(Routing(self.assemblyForward).using('requestCnt', 'response', 'responseCnt', request=RequestHTTP).
                         excluded('assemblage', 'Content'),
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
        
        data = Data()
        data.keyargs = keyargs
        data.assemblage = assemblage
        data.processingForward, data.processingContent = processingForward, processingContent
        data.Request, data.RequestContent = request.__class__, requestCnt.__class__
        data.Response, data.ResponseContent = response.__class__, responseCnt.__class__
        data.Content = Content
        data.clientIP, data.scheme = request.clientIP, request.scheme
        data.headers = dict(request.headers) if request.headers else {}
        
        remove(data.headers, self.innerHeadersRemove)
        
        chain.process(_data=data, content=Content())
        chain.branch(processingContent).onFinalize(self.processFinalize)
        chain.branch(processingForward)
        
    def processFinalize(self, final, response, responseCnt, assemblage, content, _data, **keyargs):
        '''
        Process the data.
        '''
        assert isinstance(final, Execution), 'Invalid final execution %s' % final
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        assert isinstance(content, ContentResponse), 'Invalid content %s' % content
        assert isinstance(_data, Data), 'Invalid data %s' % _data

        if content.charSet: _data.charSet = codecs.lookup(content.charSet).name
        else: _data.charSet = codecs.lookup(self.charSetDefault).name
        assemblage.main = self.populate(_data, content, response, responseCnt)
        assemblage.doRequest = self.createRequest(_data)
        del final.arg._data
        
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
            
        if ResponseContentHTTP.source not in responseCnt or responseCnt.source is None:
            content.errorStatus, content.errorText = UNAVAILABLE
            return content
        
        if isinstance(responseCnt.source, IInputStream): content.source = responseCnt.source
        elif isinstance(responseCnt.source, Iterable): content.source = StreamOnIterable(responseCnt.source)
        
        if content.charSet: charSet = codecs.lookup(content.charSet).name
        else: charSet = codecs.lookup(self.charSetDefault).name
        content.doEncode = self.createEncode(data, charSet)
        content.doDecode = self.createDecode(charSet)
        
        if not isSuccess(response.status):
            content.errorStatus = response.status
            if ResponseHTTP.text in response and response.text: content.errorText = response.text
            elif ResponseHTTP.code in response and response.code: content.errorText = response.code
        
        return content
            
    def createEncode(self, data, charSet):
        '''
        Create the encoder.
        
        @param data: Data
            The data to use for encode.
        @param charSet: string
            The character set that the bytes are encoded in.
        '''
        assert isinstance(data, Data), 'Invalid data %s' % data
        assert isinstance(data.assemblage, Assemblage), 'Invalid assemblage %s' % data.assemblage
        assert isinstance(data.charSet, str), 'Invalid assemblage character set %s' % data.charSet
        assert isinstance(charSet, str), 'Invalid character set %s' % charSet
        def doEncode(content):
            '''
            Do encode for the provided bytes.
            '''
            if isinstance(content, str): return content.encode(data.charSet, self.encodingError)
            else:
                if data.charSet == charSet: return content
                return str(content, charSet).encode(data.charSet, self.encodingError)
        return doEncode
    
    def createDecode(self, charSet):
        '''
        Create the decoder.
        
        @param charSet: string
            The character set that the bytes are encoded in.
        '''
        assert isinstance(charSet, str), 'Invalid character set %s' % charSet
        def doDecode(content):
            '''
            Do encode for the provided bytes.
            '''
            return str(content, encoding=charSet, errors=self.encodingError)
        return doDecode
    
    def createRequest(self, data):
        '''
        Create the requests handler.
        
        @param data: Data
            The data to use for dispatching the request.
        '''
        assert isinstance(data, Data), 'Invalid data %s' % data
        assert isinstance(data.Content, ContextMetaClass), 'Invalid content class %s' % data.Content
        assert isinstance(data.assemblage, Assemblage), 'Invalid assemblage %s' % data.assemblage
        def doRequest(url, parameters=None):
            '''
            Do request.
            '''
            assert isinstance(url, str), 'Invalid URL %s' % url
            assert parameters is None or isinstance(parameters, list), 'Invalid parameters %s' % parameters
            
            request = data.Request()
            assert isinstance(request, RequestHTTP), 'Invalid request %s' % request
            
            rurl = urlsplit(url)
            
            params = parse_qsl(rurl.query, True, False)
            if parameters: params.extend(parameters)
            
            request.clientIP, request.scheme, request.method = data.clientIP, data.scheme, HTTP_GET
            request.headers = dict(data.headers)
            request.uri, request.parameters = rurl.path.lstrip('/'), params
            
            proc = data.processingForward
            assert isinstance(proc, Processing), 'Invalid processing %s' % proc
            argf = proc.execute(request=request, requestCnt=data.RequestContent(), response=data.Response(),
                                responseCnt=data.ResponseContent(), **data.keyargs)
            
            proc = data.processingContent
            assert isinstance(proc, Processing), 'Invalid processing %s' % proc
            argc = proc.execute(response=argf.response, assemblage=data.assemblage, content=data.Content())
                    
            return self.populate(data, argc.content, argf.response, argf.responseCnt)
        return doRequest

# --------------------------------------------------------------------

class Data:
    '''
    The data container used in processing.
    '''
    __slots__ = ('keyargs', 'assemblage', 'processingForward', 'processingContent', 'Response', 'ResponseContent', 'Request',
                 'RequestContent', 'Content', 'clientIP', 'scheme', 'headers', 'charSet')
    if False:
        # Just for auto complete.
        keyargs = dict  # The chain key arguments in which the request is handled
        assemblage = Assemblage  # The assemblage containing data to use for content populating.
        processingForward = Processing  # The processing used for solving the request.
        processingContent = Processing  # The assembly to be used in handling the content.
        Response = ContextMetaClass  # The response context.
        ResponseContent = ContextMetaClass  # The response content context.
        Request = ContextMetaClass  # The request context.
        RequestContent = ContextMetaClass  # The request content context.
        Content = ContextMetaClass  # The content context class used in constructing the returned objects.
        clientIP = str  # The client IP used for inner requests.
        scheme = str  # The scheme used for inner requests.
        headers = dict  # The headers to be used for inner requests.
        charSet = str  # The character set that the response need to be encoded in.
