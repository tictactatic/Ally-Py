'''
Created on Mar 27, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assembler processor.
'''

from ally.assemblage.http.spec.assemblage import IRepository, Matcher
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.branch import Using
from ally.design.processor.context import Context, pushIn
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranchingProceed
from ally.http.spec.codes import isSuccess
from ally.http.spec.server import IDecoderHeader, ResponseContentHTTP, \
    ResponseHTTP, RequestHTTP, HTTP_GET
from ally.support.util_io import IInputStream
from codecs import getreader, getwriter
from io import BytesIO
from urllib.parse import urlsplit, parse_qsl
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    method = requires(str)
    headers = requires(dict)
    uri = requires(str)
    repository = requires(IRepository)
    decoderHeader = requires(IDecoderHeader)

class ResponseContentData(ResponseContentHTTP):
    '''
    The response content context containing data for assemblage.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)
    charSet = requires(str)

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
        super().__init__(Using(self.assembly, 'request', 'requestCnt', response=ResponseHTTP, responseCnt=ResponseContentData))

    def process(self, processing, request:Request, requestCnt:Context, response:Context, responseCnt:Context, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Assemble response content.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid decoder header %s' % request.decoderHeader
        
        names = request.decoderHeader.decode(self.nameAssemblage)
        uri = request.uri  # We capture the URI here since it might be change by internal processing.
        
        isOk, responseData, responseCntData = processResponse(processing, request, requestCnt)
        assert isinstance(responseCntData, ResponseContentData), 'Invalid response content %s' % responseCntData
        
        pushIn(response, responseData)
        pushIn(responseCnt, responseCntData)
        
        if not isOk: return
        # The main request has failed or has no content or no assemblage, nothing to do just move along.
        if not names: return
        # There are no assemblages required, nothing to do just move along.
        
        assert isinstance(request.repository, IRepository), 'Invalid repository %s' % request.repository
        matchers = request.repository.matchers(responseCntData.type, request.method, uri, request.headers)
        if not matchers: return
        # No matchers to process, nothing to do.
        
        def fetchContentForURI(uri):
            url = urlsplit(uri)
            requestRef = processing.ctx.request()
            assert isinstance(requestRef, RequestHTTP), 'Invalid request %s' % requestRef
            
            requestRef.scheme = request.scheme
            requestRef.method = HTTP_GET
            requestRef.headers = dict(request.headers)
            requestRef.uri = url.path.lstrip('/')
            requestRef.parameters = parse_qsl(url.query, True, False)
            
            isOk, _response, responseCntRef = processResponse(processing, requestRef)
            if not isOk:
                # TODO: see how to behave here
                return
            return fetchContent(responseCntRef)
        
        names = set(name for name, _attr in names)
        
        matchersSelected, index = [], 0
        for name in names:
            for matcher in matchers:
                assert isinstance(matcher, Matcher), 'Invalid matcher %s' % matcher
                if len(matcher.names) > index and name == matcher.names[index]:
                    matchersSelected.append(matcher)
                    break
        
        if not matchersSelected: return
        # No valid matchers have been selected, moving along.
        
        content = fetchContent(responseCnt)
        if not content:
            # TODO: see how to behave here
            return
        
        assembled = self.processMatchers(matchersSelected, 0, content, fetchContentForURI)
        pushContent(responseCnt, ''.join(assembled))
        
    # ----------------------------------------------------------------
    
    def processMatchers(self, matchers, index, content, fetchContentForURI):
        '''
        Process the assemble.
        '''
        assert isinstance(matchers, list), 'Invalid matchers %s' % matchers
        assert isinstance(index, int), 'Invalid index %s' % index
        assert isinstance(content, str), 'Invalid content %s' % content
        assert callable(fetchContentForURI), 'Invalid fetcher %s' % fetchContentForURI
        
        matcher = matchers[index]
        assert isinstance(matcher, Matcher), 'Invalid matcher %s' % matcher
        
        assembled, current, hasMore = [], 0, index + 1 < len(matchers)
        for match in matcher.pattern.finditer(content):
            if hasMore:
                assembled.extend(self.processMatchers(matchers, index + 1, content[current:match.start()], fetchResponse))
            else:
                assembled.append(content[current:match.start()])
            current = match.end()
            
            if matcher.reference:
                matchRef = matcher.reference.search(match.group())
                if matchRef:
                    for reference in matchRef.groups():
                        if reference: break
                    else:
                        # TODO: see how to behave here
                        continue
                    
                    contentRef = fetchResponse(reference)
                    if not contentRef:
                        # TODO: see how to behave here
                        continue
                    
                    if matcher.adjustPattern and matcher.adjustReplace:
                        for replacer, value in zip(matcher.adjustReplace, matcher.adjustPattern):
                            for k, group in enumerate(match.groups()):
                                value = value.replace('{%s}' % (k + 1), group)
                            contentRef = replacer.sub(value, contentRef)
                            
                    assembled.append(contentRef)
        
        if hasMore:
            assembled.extend(self.processMatchers(matchers, index + 1, content[current:], fetchResponse))
        else:
            assembled.append(content[current:])
        return assembled

# --------------------------------------------------------------------

def processResponse(processing, request, requestCnt=None):
    '''
    Get the response for the request.
    
    @param processing: Processing
        The processing used for delivering the request.
    @param request: RequestHTTP
        The request object to deliver.
    @return: tuple(boolean, ResponseHTTP, ResponseContentHTTP)
        A tuple of three containing a flag indicating the success status and then the response and response content.
    '''
    assert isinstance(processing, Processing), 'Invalid processing %s' % processing
    
    if requestCnt is None: requestCnt = processing.ctx.requestCnt()
    chain = Chain(processing)
    chain.process(request=request, requestCnt=requestCnt,
                  response=processing.ctx.response(), responseCnt=processing.ctx.responseCnt()).doAll()

    response, responseCnt = chain.arg.response, chain.arg.responseCnt
    assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
    assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
    
    isOk = ResponseContentHTTP.source in responseCnt and responseCnt.source is not None and isSuccess(response.status)
    return isOk, response, responseCnt

def fetchContent(responseCnt):
    '''
    Fetches the text content into a string, None if the content type is no usable.
    
    @param responseCnt: ResponseContentData
        The response content to fetch the content from.
    @return: string|None
        The content or None if there is a problem.
    '''
    assert isinstance(responseCnt, ResponseContentData), 'Invalid response content %s' % responseCnt
    
    try: decoder = getreader(responseCnt.charSet)
    except LookupError: return
    
    if isinstance(responseCnt.source, IInputStream):
        source = responseCnt.source
    else:
        source = BytesIO()
        for bytes in responseCnt.source: source.write(bytes)
        source.seek(0)
    
    return decoder(source).read()
        
def pushContent(responseCnt, content):
    '''
    Pushes the text content into the response content.
    
    @param responseCnt: ResponseContentData
        The response content to push the content to.
    @param content: string
        The content to push in the response content.
    '''
    assert isinstance(responseCnt, ResponseContentData), 'Invalid response content %s' % responseCnt
    assert isinstance(content, str), 'Invalid content %s' % content
    
    source = BytesIO()
    encoder = getwriter(responseCnt.charSet)(source)
    encoder.write(content)
    source.seek(0)
    responseCnt.source = source
