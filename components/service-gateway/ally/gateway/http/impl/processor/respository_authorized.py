'''
Created on Apr 12, 2012

@package: gateway service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the gateway repository processor.
'''

from . import respository
from .respository import GatewayRepositoryHandler, Repository, Identifier, \
    Response
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.gateway.http.spec.gateway import IRepository, RepositoryJoined
from ally.http.spec.codes import BAD_REQUEST, BAD_GATEWAY, INVALID_AUTHORIZATION, \
    isSuccess
from ally.http.spec.server import IDecoderHeader
from datetime import datetime, timedelta
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(respository.Request):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    match = defines(Context, doc='''
    @rtype: Context
    The error match in case of failure.
    ''')
    # ---------------------------------------------------------------- Required
    method = requires(str)
    headers = requires(dict)
    uri = requires(str)
    decoderHeader = requires(IDecoderHeader)

# --------------------------------------------------------------------

@injected
class GatewayAuthorizedRepositoryHandler(GatewayRepositoryHandler):
    '''
    Extension for @see: GatewayRepositoryHandler that provides the service for authorized gateways.
    '''
    
    nameAuthorization = 'Authorization'
    # The header name for the session identifier.
    
    def __init__(self):
        assert isinstance(self.nameAuthorization, str), 'Invalid authorization name %s' % self.nameAuthorization
        super().__init__()
        
        self._timeOut = timedelta(seconds=self.cleanupInterval)

    def process(self, processing, request:Request, response:Response, Gateway:Context, Match:Context, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Obtains the repository.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        if response.isSuccess is False: return  # Skip in case the response is in error
        
        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid decoder header %s' % request.decoderHeader
        authentication = request.decoderHeader.retrieve(self.nameAuthorization)
        if not authentication: return
        
        repository = self._repositories.get(authentication)
        if repository is None:
            robj, status, text = self.obtainGateways(processing, self.uri % authentication)
            if robj is None or not isSuccess(status):
                if status == BAD_REQUEST.status:
                    response.code, response.status, response.isSuccess = INVALID_AUTHORIZATION
                    if request.repository:
                        assert isinstance(request.repository, IRepository), 'Invalid repository %s' % request.repository
                        request.match = request.repository.find(request.method, request.headers, request.uri,
                                                                INVALID_AUTHORIZATION.status)
                else:
                    log.info('Cannot fetch the authorized gateways from URI \'%s\', with response %s %s', self.uri, status, text)
                    response.code, response.status, response.isSuccess = BAD_GATEWAY
                    response.text = text
                return
            assert 'GatewayList' in robj, 'Invalid objects %s, not GatewayList' % robj
            repository = Repository([self.populate(Identifier(Gateway()), obj) for obj in robj['GatewayList']], Match)
            self._repositories[authentication] = repository
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
