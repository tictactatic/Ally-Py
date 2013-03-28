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
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Using
from ally.design.processor.context import Context, pushIn
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranchingProceed
from ally.http.spec.codes import isSuccess
from ally.http.spec.server import IDecoderHeader, ResponseHTTP, RequestHTTP, \
    HTTP_GET
from ally.support.util_io import IInputStream
from codecs import getreader, getwriter
from collections import Iterable
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
    scheme = requires(str)
    method = requires(str)
    headers = requires(dict)
    uri = requires(str)
    repository = requires(IRepository)
    decoderHeader = requires(IDecoderHeader)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defined
    length = defines(int)
    
class ResponseContentData(Context):
    '''
    The response content context containing data for assemblage.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)
    charSet = requires(str)
    source = requires(IInputStream, Iterable)

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

    def process(self, processing, request:Request, requestCnt:Context, response:Context,
                responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Assemble response content.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid decoder header %s' % request.decoderHeader
        
        names = request.decoderHeader.decode(self.nameAssemblage)
        if names:
            # We capture the URI and data here since the data on request might be change by internal processing.
            uri, data = request.uri, dict(scheme=request.scheme, headers=dict(request.headers))
            names = set(name for name, _attr in names)
        
        isOk, responseData, responseCntData = self.fetchResponse(processing, request, requestCnt)
        assert isinstance(responseCntData, ResponseContentData), 'Invalid response content %s' % responseCntData
        
        pushIn(response, responseData)
        pushIn(responseCnt, responseCntData)
        assert isinstance(responseCnt, ResponseContentData), 'Invalid response content %s' % responseCnt
        
        if not isOk or not names: return
        # The main request has failed or has no content or no assemblages required, nothing to do just move along.
        
        assert isinstance(request.repository, IRepository), 'Invalid repository %s' % request.repository
        matchers = request.repository.matchers(responseCnt.type, request.method, uri, request.headers)
        if not matchers: return
        # No matchers to process, nothing to do.
        matchers = self.associateMatchers(names, matchers, True)
        if not matchers: return
        # No valid matchers have been selected, moving along.
        
        content, error = self.fetchContent(responseCnt)
        if not content:
            log.warn('Cannot fetch content for \'%s\' because: %s', uri, error)
            return
        
        data.update(processing=processing, repository=request.repository, contentType=responseCnt.type)
        assembled = self.assemble(matchers, content, data)
        
        source = BytesIO()
        encoder = getwriter(responseCnt.charSet)(source)
        for content in assembled: encoder.write(content)
        responseCnt.length = source.tell()
        source.seek(0)
        responseCnt.source = source
        
    # ----------------------------------------------------------------
        
    def fetchResponse(self, processing, request, requestCnt=None):
        '''
        Fetch the response for the request.
        
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
        assert isinstance(responseCnt, ResponseContentData), 'Invalid response content %s' % responseCnt
        
        isOk = ResponseContentData.source in responseCnt and responseCnt.source is not None and isSuccess(response.status)
        return isOk, response, responseCnt
    
    def fetchContent(self, responseCnt):
        '''
        Fetches the text content into a string, None if the content type is no usable.
        
        @param responseCnt: ResponseContentData
            The response content to fetch the content from.
        @return: tuple(string|None, string|None)
            A tuple of two, on the first position the content string or None if a problem occurred and on the second position
            the error explanation if there was a problem.
        '''
        assert isinstance(responseCnt, ResponseContentData), 'Invalid response content %s' % responseCnt
        
        try: decoder = getreader(responseCnt.charSet)
        except LookupError: return None, 'Unknown encoding \'%s\'' % responseCnt.charSet
        
        if isinstance(responseCnt.source, IInputStream):
            source = responseCnt.source
        else:
            source = BytesIO()
            for bytes in responseCnt.source: source.write(bytes)
            source.seek(0)
        
        return decoder(source).read(), None
    
    def associateMatchers(self, names, matchers, isMain=False):
        '''
        Provides the matchers that are associated with the provided names.
        
        @param names: Iterable(string)
            The set of names to associate with the matchers.
        @param matchers: Iterable(Matcher)
            The matchers to associate with.
        @param isMain: boolean
            Flag indicating that the matchers should be associated for the main response.
        @return: list[tuple(Matcher, boolean, list[string]|None)]|None
            A list of tuples containing on the first position the matcher, next the flag indicating that the matcher content
            should be excluded or included and last the names to be fetched inside the matcher assembly if there are any,
            basically (matcher, include(True) or exclude(False), sub names)
            None if no matchers could be associated.
        '''
        assert isinstance(names, Iterable), 'Invalid names %s' % names
        assert isinstance(matchers, Iterable), 'Invalid matchers %s' % matchers
        assert isinstance(isMain, bool), 'Invalid is main flag %s' % isMain
        
        names, matchers, matchersByName, subNamesForName, missing = list(names), iter(matchers), {}, {}, []
        for matcher in matchers:
            assert isinstance(matcher, Matcher), 'Invalid matcher %s' % matcher
            isFound, k = False, 0
            while k < len(names):
                name = names[k]
                assert isinstance(name, str), 'Invalid name %s' % name
                if name == matcher.name:
                    isFound = True
                    matchersByName[name] = matcher
                    del names[k]
                elif name.startswith(matcher.namePrefix):
                    isFound = True
                    name, sname = name[:len(matcher.namePrefix) - 1], name[len(matcher.namePrefix):]
                    matchersByName[name] = matcher
                    subNames = subNamesForName.get(name)
                    if subNames is None: subNames = subNamesForName[name] = []
                    subNames.append(sname)
                    del names[k]
                else: k += 1
            if not isFound: missing.append(matcher)
            if not names:
                missing.extend(matchers)
                break
        
        if '*' in names:
            for matcher in missing: matchersByName[matcher.name] = matcher
            missing = ()
            
        
        if not matchersByName: return
        
        associated = []
        for name, matcher in matchersByName.items():
            subNames = subNamesForName.get(name)
            if subNames:
                if matcher.present:
                    assert isinstance(matcher.present, set)
                    if matcher.present.issuperset(subNames): continue
                    # If the sub names are already present then no need to add the matcher.
                
            associated.append((matcher, True, subNames))
            
        if not isMain:
            for matcher in missing: associated.append((matcher, False, None))
        
        return associated
    
    # ----------------------------------------------------------------
        
    def assemble(self, matchers, content, data):
        '''
        Process the assemble.
        '''
        assert isinstance(matchers, list), 'Invalid matchers %s' % matchers
        assert isinstance(content, str), 'Invalid content %s' % content
        assert isinstance(data, dict), 'Invalid data %s' % data
        
        while matchers:
            matcher, include, names = matchers.pop()
            assert isinstance(matcher, Matcher), 'Invalid matcher %s' % matcher
            
            if not include: break  # We need to exclude the matchers block so proceed with the matcher.
            if matcher.reference and names: break  # We need to process the reference so proceed with the matcher
        else:
            # No matcher needs processing
            return (content,)
        
        assembled, current = [], 0
        for match in matcher.pattern.finditer(content):
            mcontent = content[current:match.start()]
            if matchers: assembled.extend(self.assemble(list(matchers), mcontent, data))
            else: assembled.append(mcontent)
            current = match.end()
            
            if not include: continue  # We exclude the block
            
            block = match.group()
            rmatch = matcher.reference.search(block)
            if rmatch:
                for reference in rmatch.groups():
                    if reference: break
                else:
                    assert log.debug('No URI reference located in:\n%s', block) or True
                    assembled.append(block)
                    continue
                
                rurl = urlsplit(reference)
                ruri = rurl.path.lstrip('/')
                rparameters = parse_qsl(rurl.query, True, False)
                
                smatchers = self.matchersForURI(ruri, names, **data)
                if not smatchers:
                    # No matchers to process on the reference content
                    assembled.append(block)
                    continue
                
                rcontent, error = self.fetchForURI(ruri, rparameters, **data)
                if not rcontent:
                    log.warn('Cannot fetch content for \'%s\' because: %s', ruri, error)
                    # TODO: see how to behave here
                    continue
                
                sassembled = self.assemble(smatchers, rcontent, data)
                rcontent = ''.join(sassembled)
                
                groups = match.groups()
                if matcher.adjustPattern and matcher.adjustReplace:
                    for replacer, value in zip(matcher.adjustReplace, matcher.adjustPattern):
                        for k, group in enumerate(groups):
                            value = value.replace('{%s}' % (k + 1), group)
                        rcontent = replacer.sub(value, rcontent)
                
                assembled.append(rcontent)
        
        mcontent = content[current:]
        if matchers: assembled.extend(self.assemble(matchers, mcontent, data))
        else: assembled.append(mcontent)
        
        return assembled
        
    def fetchForURI(self, uri, parameters, processing, scheme, headers, **data):
        '''
        Fetches the content for the provided URI.
        
        @param uri: string
            The URI to fetch the content for.
        @param parameters: list[tuple(string, string)]
            The parameters of the URI.
        @param processing: Processing
            The processing to use for the request.
        @param scheme: string
            The scheme for the request.
        @param headers: dictionary{string: string}
            The headers to use on the request.
        @return: tuple(string|None, string|None)
            A tuple of two, on the first position the content string or None if a problem occurred and on the second position
            the error explanation if there was a problem.
        '''
        assert isinstance(uri, str), 'Invalid uri %s' % uri
        assert isinstance(parameters, list), 'Invalid parameters %s' % parameters
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(scheme, str), 'Invalid scheme %s' % scheme
        assert isinstance(headers, dict), 'Invalid headers %s' % headers
        
        request = processing.ctx.request()
        assert isinstance(request, RequestHTTP), 'Invalid request %s' % request
        
        request.scheme = scheme
        request.method = HTTP_GET
        request.headers = dict(headers)
        request.uri = uri
        request.parameters = parameters
        
        isOk, response, responseCnt = self.fetchResponse(processing, request)
        if not isOk:
            assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
            if ResponseHTTP.text in response and response.text: text = response.text
            elif ResponseHTTP.code in response and response.code: text = response.code
            else: text = None
            
            if text: text = '%s %s' % (response.status, text)
            else: text = str(response.status)
            return None, text
        return self.fetchContent(responseCnt)
    
    def matchersForURI(self, uri, names, repository, contentType, headers, **data):
        '''
        Provides the matchers obtained for URI directly associated with the provided names.
        
        @param uri: string
            The URI to get the matchers for.
        @param names: set(string)|list[string]
            The set of names to associate with the URI matchers.
        @param repository: IRepository
            The repository used in getting the URI matchers.
        @param contentType: string
            The content type to process the matchers for.
        @param headers: dictionary{string: string}
            The headers to to be used on the matchers.
        @return: dictionary{Matcher: list[string]|None}|None
            A dictionary with the associated matchers and as a value the list of sub names to be processed for that matcher.
            None if there is no avaialable matchers for URI.
        '''
        assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
        matchers = repository.matchers(contentType, HTTP_GET, uri, headers)
        if not matchers: return
        # No matchers to process, nothing to do.
        return self.associateMatchers(names, matchers)
         
