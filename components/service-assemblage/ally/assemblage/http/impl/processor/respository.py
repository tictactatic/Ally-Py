'''
Created on Apr 12, 2012

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblage repository processor.
'''

from ally.assemblage.http.spec.assemblage import IRepository, Assemblage, \
    Identifier, Matcher
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines
from ally.design.processor.branch import Using
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranchingProceed
from ally.http.spec.codes import isSuccess
from ally.http.spec.server import RequestHTTP, ResponseHTTP, ResponseContentHTTP, \
    HTTP_GET, HTTP
from ally.support.util_io import IInputStream
from functools import partial
from io import BytesIO
from urllib.parse import urlparse, parse_qsl
import codecs
import json
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    repository = defines(IRepository)

# --------------------------------------------------------------------

class RequestResource(RequestHTTP):
    '''
    The request resource context.
    '''
    # ---------------------------------------------------------------- Defined
    accTypes = defines(list)
    accCharSets = defines(list)

# --------------------------------------------------------------------

@injected
class AssemblageRepositoryHandler(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the assemblage repository by using REST data received from either internal or
    external server. The Assemblage structure is defined as in the @see: assemblage plugin.
    '''
    
    scheme = HTTP
    # The scheme to be used in fetching the resource objects.
    mimeTypeJson = 'json'
    # The json mime type to be sent for the resource requests.
    encodingJson = 'utf-8'
    # The json encoding to be sent for the resource requests.
    uri = str
    # The URI used in fetching the assemblages.
    assembly = Assembly
    # The assembly to be used in processing the request for the resource.
    
    def __init__(self):
        assert isinstance(self.scheme, str), 'Invalid scheme %s' % self.scheme
        assert isinstance(self.mimeTypeJson, str), 'Invalid json mime type %s' % self.mimeTypeJson
        assert isinstance(self.encodingJson, str), 'Invalid json encoding %s' % self.encodingJson
        assert isinstance(self.uri, str), 'Invalid URI %s' % self.uri
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Using(self.assembly, 'requestCnt', 'response', 'responseCnt', request=RequestResource))
        
        self._structure = None

    def process(self, processing, request:Request, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Obtains the repository.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        
        if not self._structure:
            robjs, status, text = self.obtainResource(processing, self.uri)
            if robjs is None or not isSuccess(status):
                log.error('Cannot fetch the assemblages from URI \'%s\', with response %s %s', self.uri, status, text)
                return
            self._structure = Structure(robjs)
            
        request.repository = Repository(self._structure, partial(self.obtainResource, processing))
        
    # ----------------------------------------------------------------
   
    def obtainResource(self, processing, uri):
        '''
        Get the resource objects representation.
        
        @param processing: Processing
            The processing used for delivering the request.
        @param uri: string
            The URI to call, parameters are allowed.
        @return: tuple(dictionary{...}|None, integer, string)
            A tuple containing as the first position the resources objects representation, None if the resources cannot 
            be fetched, on the second position the response status and on the last position the response text.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(uri, str), 'Invalid URI %s' % uri
        
        request = processing.ctx.request()
        assert isinstance(request, RequestResource), 'Invalid request %s' % request
        
        url = urlparse(uri)
        request.scheme, request.method = self.scheme, HTTP_GET
        request.headers = {}
        request.uri = url.path.lstrip('/')
        request.parameters = parse_qsl(url.query, True, False)
        request.accTypes = [self.mimeTypeJson]
        request.accCharSets = [self.encodingJson]
        
        chain = Chain(processing)
        chain.process(request=request, requestCnt=processing.ctx.requestCnt(),
                      response=processing.ctx.response(), responseCnt=processing.ctx.responseCnt()).doAll()

        response, responseCnt = chain.arg.response, chain.arg.responseCnt
        assert isinstance(response, ResponseHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContentHTTP), 'Invalid response content %s' % responseCnt
        
        if ResponseHTTP.text in response and response.text: text = response.text
        elif ResponseHTTP.code in response and response.code: text = response.code
        else: text = None
        if ResponseContentHTTP.source not in responseCnt or responseCnt.source is None or not isSuccess(response.status):
            return None, response.status, text
        
        if isinstance(responseCnt.source, IInputStream):
            source = responseCnt.source
        else:
            source = BytesIO()
            for bytes in responseCnt.source: source.write(bytes)
            source.seek(0)
        return json.load(codecs.getreader(self.encodingJson)(source)), response.status, text

# --------------------------------------------------------------------

class Structure:
    '''
    Structure containing the assemblage objects.
    '''
    __slots__ = ('assemblages', 'identifiersByAssemblage', 'matchersByIdentifier')
    
    def __init__(self, robjs):
        '''
        Construct the assemblage structure based on the provided dictionary object.
        
        @param objs: dictionary{string: list[dictionary{...}]}
            The dictionary used for defining the structure assemblage, the objects as is defined from response.
        '''
        assert isinstance(robjs, dict), 'Invalid objects %s' % robjs
        assert 'AssemblageList' in robjs, 'Invalid objects %s, no AssemblageList' % robjs
        
        self.assemblages = [Assemblage(obj) for obj in robjs['AssemblageList']]
        self.identifiersByAssemblage = {}
        self.matchersByIdentifier = {}

class Repository(IRepository):
    '''
    The assemblage repository.
    '''
    __slots__ = ('_structure', '_obtain')
    
    def __init__(self, structure, obtain):
        '''
        Construct the assemblage repository.
        
        @param structure: Structure
            The structure containing the assemblage objects.
        @param obtain: callable(string) -> tuple(dictionary{...}|None, integer, string)
            The callable that provides additional resources.
        '''
        assert isinstance(structure, Structure), 'Invalid structure %s' % structure
        assert callable(obtain), 'Invalid obtain call %s' % obtain
        
        self._structure = structure
        self._obtain = obtain
    
    def matchers(self, forType, method, uri, headers=None):
        '''
        @see: IRepository.matchers
        '''
        assert isinstance(forType, str), 'Invalid type %s' % forType
        assert isinstance(method, str), 'Invalid method %s' % method
        assert isinstance(uri, str), 'Invalid uri %s' % uri
        
        strct = self._structure
        assert isinstance(strct, Structure)
        
        forType = forType.lower()
        for assemblage in strct.assemblages:
            assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
            if forType in assemblage.types: break
        else:
            assert log.debug('No assemblage available for %s', forType) or True
            return
        
        identifiers = strct.identifiersByAssemblage.get(assemblage.id)
        if identifiers is None:
            robjs, status, text = self._obtain(assemblage.hrefIdentifiers)
            if robjs is None or not isSuccess(status):
                log.error('Cannot fetch the identifiers from URI \'%s\', with response %s %s',
                          assemblage.hrefIdentifiers, status, text)
                return
            assert isinstance(robjs, dict), 'Invalid objects %s' % robjs
            assert 'IdentifierList' in robjs, 'Invalid objects %s, no IdentifierList' % robjs
            identifiers = [Identifier(obj) for obj in robjs['IdentifierList']]
            strct.identifiersByAssemblage[assemblage.id] = identifiers
        
        method = method.upper()
        for identifier in identifiers:
            assert isinstance(identifier, Identifier), 'Invalid identifier %s' % identifier
            if method != identifier.method: continue
            if not identifier.pattern.match(uri): continue
            if headers is not None:
                assert isinstance(headers, dict), 'Invalid headers %s' % uri
                isExcluded = False
                if identifier.headersExclude:
                    for nameValue in headers.items():
                        header = '%s:%s' % nameValue
                        for pattern in identifier.headersExclude:
                            if pattern.match(header):
                                isExcluded = True
                                break
                        if isExcluded: break
                    if isExcluded: continue
            break
        else:
            assert log.debug('No identifier available for method \'%s\', and URI \'%s\'', forType, uri) or True
            return
        
        matchers = strct.matchersByIdentifier.get(identifier.id)
        if matchers is None:
            robjs, status, text = self._obtain(identifier.hrefMatchers)
            if robjs is None or not isSuccess(status):
                log.error('Cannot fetch the matchers from URI \'%s\', with response %s %s',
                          identifier.hrefMatchers, status, text)
                return
            assert isinstance(robjs, dict), 'Invalid objects %s' % robjs
            assert 'MatcherList' in robjs, 'Invalid objects %s, no MatcherList' % robjs
            matchers = [Matcher(obj) for obj in robjs['MatcherList']]
            strct.matchersByIdentifier[identifier.id] = matchers
        
        if not matchers: return
        return iter(matchers)
