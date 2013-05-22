'''
Created on Apr 12, 2012

@package: gateway service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the gateway repository processor.
'''

from .respository import GatewayRepositoryHandler, Repository
from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.execution import Processing
from ally.gateway.http.spec.gateway import IRepository, Match
from ally.http.spec.codes import BAD_REQUEST, BAD_GATEWAY, INVALID_AUTHORIZATION, \
    CodedHTTP
from ally.http.spec.headers import HeaderRaw, HeadersRequire
from ally.support.http.util_dispatch import obtainJSON
from datetime import datetime, timedelta
from urllib.parse import quote
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

AUTHORIZATION = HeaderRaw('Authorization')
# The header for the session identifier. 

# --------------------------------------------------------------------

class Request(HeadersRequire):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    repository = defines(IRepository)
    match = defines(Match)
    # ---------------------------------------------------------------- Required
    decoderHeader = requires(IDecoderHeader)

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)

# --------------------------------------------------------------------

@injected
class GatewayAuthorizedRepositoryHandler(GatewayRepositoryHandler):
    '''
    Extension for @see: GatewayRepositoryHandler that provides the service for authorized gateways.
    '''
    
    def __init__(self):
        super().__init__()
        
        self._timeOut = timedelta(seconds=self.cleanupInterval)

    def process(self, chain, processing, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Obtains the repository.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        if response.isSuccess is False: return  # Skip in case the response is in error
        
        authentication = AUTHORIZATION.fetch(request)
        if not authentication: return
        
        repository = self._repositories.get(authentication)
        if repository is None:
            jobj, status, _text = obtainJSON(processing, self.uri % quote(authentication), details=True)
            if jobj is None:
                if status == BAD_REQUEST.status: INVALID_AUTHORIZATION.set(response)
                else: BAD_GATEWAY.set(response)
                return
            repository = self._repositories[authentication] = Repository(jobj)
        self._lastAccess[authentication] = datetime.now()
        
        if request.repository: request.repository = RepositoryJoined(repository, request.repository)
        else: request.repository = repository
    
    # ----------------------------------------------------------------
    
    def initialize(self):
        '''
        @see: GatewayRepositoryHandler.initialize
        '''
        self._repositories = {}
        self._lastAccess = {}
        self.startCleanupThread('Cleanup authorized gateways thread')

    def performCleanup(self):
        '''
        @see: GatewayRepositoryHandler.performCleanup
        '''
        current, expired = datetime.now() - self._timeOut, []
        for authentication, lastAccess in self._lastAccess.items():
            if current > lastAccess: expired.append(authentication)
        
        assert log.debug('Clearing %s sessions at %s' % (len(expired), datetime.now())) or True
        for authentication in expired:
            self._repositories.pop(authentication, None)
            self._lastAccess.pop(authentication, None)

# --------------------------------------------------------------------

class RepositoryJoined(IRepository):
    '''
    Repository that uses other repositories to provide services.
    '''
    __slots__ = ('_repositories',)
    
    def __init__(self, main, *repositories):
        '''
        Construct the joined repositories.
        
        @param main: IRepository
            The main repository, this will be used for storing caches.
        @param repositories: arguments[IRepository]
            The repositories to join with the main repositories.
        '''
        assert isinstance(main, IRepository), 'Invalid main repository %s' % main
        assert repositories, 'At least one other repository is required for joining'
        if __debug__:
            for repository in repositories: assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
        
        self._repositories = [main]
        self._repositories.extend(repositories)
        
    def find(self, method=None, headers=None, uri=None, error=None):
        '''
        @see: IRepository.find
        '''
        for repository in self._repositories:
            assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
            match = repository.find(method, headers, uri, error)
            if match is not None: return match
        
    def allowsFor(self, headers=None, uri=None):
        '''
        @see: IRepository.allowsFor
        '''
        allowed = set()
        for repository in self._repositories:
            assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
            allowed.update(repository.allowsFor(headers, uri))
        return allowed
        
    def obtainCache(self, identifier):
        '''
        @see: IRepository.obtainCache
        '''
        return self._repositories[0].obtainCache(identifier)
