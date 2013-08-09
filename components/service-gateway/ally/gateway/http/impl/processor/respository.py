'''
Created on Apr 12, 2012

@package: gateway service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the gateway repository processor.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.gateway.http.spec.gateway import IRepository, RepositoryJoined
from ally.http.spec.codes import BAD_GATEWAY, CodedHTTP
from ally.http.spec.server import HTTP_OPTIONS
from ally.support.http.util_dispatch import RequestDispatch, obtainJSON
from sched import scheduler
from threading import Thread
import logging
import re
import time

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class GatewayRepository(Context):
    '''
    The gateway context based on @see: gateway-http/gateway.http.gateway
    '''
    # ---------------------------------------------------------------- Defined
    filters = defines(list, doc='''
    @rtype: list[string]
    Contains a list of URIs that need to be called in order to allow the gateway Navigate. The filters are
    allowed to have place holders of form '{1}' or '{2}' ... '{n}' where n is the number of groups obtained
    from the Pattern, the place holders will be replaced with their respective group value. All filters
    need to return a True value in order to allow the gateway Navigate, also parameters are allowed
    for filter URI.
    ''')
#    host = defines(str, doc='''
#    @rtype: string
#    The host where the request needs to be resolved, if not provided the request will be delegated to the
#    default host.
#    ''')
#    protocol = defines(str, doc='''
#    @rtype: string
#    The protocol to be used in the communication with the server that handles the request, if not provided
#    the request will be delegated using the default protocol.
#    ''')
    navigate = defines(str, doc='''
    @rtype: string
    A pattern like string of forms like '*', 'resources/*' or 'redirect/Model/{1}'. The pattern is allowed to
    have place holders and also the '*' which stands for the actual called URI, also parameters are allowed
    for navigate URI, the parameters will be appended to the actual parameters.
    ''')
    putHeaders = defines(list, doc='''
    @rtype: list[tuple(string, string)]
    The headers to be put on the forwarded requests. The values are provided as 'Name:Value', the name is
    not allowed to contain ':'.
    ''')

class MatchRepository(Context):
    '''
    The match context.
    '''
    # ---------------------------------------------------------------- Defined
    gateway = defines(Context, doc='''
    @rtype: Context
    The matched gateway.
    ''')
    groupsURI = defines(tuple, doc='''
    @rtype: tuple(string)
    The match groups for the URI.
    ''')

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    repository = defines(IRepository, doc='''
    @rtype: IRepository
    The repository to be used for finding matches.
    ''')
    # ---------------------------------------------------------------- Required
    clientIP = requires(str)
    
class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)

# --------------------------------------------------------------------

@injected
class GatewayRepositoryHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the gateway repository by using REST data received from either internal or
    external server. The Gateway structure is defined as in the @see: gateway-http plugin.
    '''
    
    uri = str
    # The URI used in fetching the gateways.
    cleanupInterval = float
    # The number of seconds to perform clean up for cached gateways.
    assembly = Assembly
    # The assembly to be used in processing the request for the gateways.
    
    def __init__(self):
        assert isinstance(self.uri, str), 'Invalid URI %s' % self.uri
        assert isinstance(self.cleanupInterval, int), 'Invalid cleanup interval %s' % self.cleanupInterval
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Branch(self.assembly).using('requestCnt', 'response', 'responseCnt', request=RequestDispatch))
        self.initialize()

    def process(self, chain, processing, request:Request, response:Response,
                Gateway:GatewayRepository, Match:MatchRepository, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Obtains the repository.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert issubclass(Gateway, GatewayRepository), 'Invalid gateway class %s' % Gateway
        assert issubclass(Match, MatchRepository), 'Invalid match class %s' % Match
        
        if self._identifiers is None:
            jobj, status, text = obtainJSON(processing, self.uri, details=True)
            if jobj is None:
                log.error('Cannot fetch the gateways from URI \'%s\', with response %s %s', self.uri, status, text)
                BAD_GATEWAY.set(response)
                response.text = text
                return
            assert 'GatewayList' in jobj, 'Invalid objects %s, not GatewayList' % jobj
            self._identifiers = [self.populate(Identifier(Gateway()), obj) for obj in jobj['GatewayList']]
            
        repository = Repository(request.clientIP, self._identifiers, Match)
        if request.repository: request.repository = RepositoryJoined(request.repository, repository)
        else: request.repository = repository

    # ----------------------------------------------------------------
    
    def initialize(self):
        '''
        Initialize the repository.
        '''
        self._identifiers = None
        self.startCleanupThread('Cleanup gateways thread')
   
    def startCleanupThread(self, name):
        '''
        Starts the cleanup thread.
        
        @param name: string
            The name for the thread.
        '''
        schedule = scheduler(time.time, time.sleep)
        def executeCleanup():
            self.performCleanup()
            schedule.enter(self.cleanupInterval, 1, executeCleanup, ())
        schedule.enter(self.cleanupInterval, 1, executeCleanup, ())
        scheduleRunner = Thread(name=name, target=schedule.run)
        scheduleRunner.daemon = True
        scheduleRunner.start()

    def performCleanup(self):
        '''
        Performs the cleanup for gateways.
        '''
        self._identifiers = None
    
    # ----------------------------------------------------------------
    
    def populate(self, identifier, obj):
        '''
        Populates the gateway based on the provided dictionary object.
        @see: gateway-http/gateway.http.gateway
        
        @param identifier: Identifier
            The identifier object to populate.
        @param obj: dictionary{string: string|list[string]}
            The dictionary used for defining the gateway object, the object as is defined from response.
        @return: Identifier
            The populated identifier object.
        '''
        assert isinstance(identifier, Identifier), 'Invalid identifier %s' % identifier
        assert isinstance(obj, dict), 'Invalid object %s' % obj
        
        clients = obj.get('Clients')
        if clients:
            assert isinstance(clients, list), 'Invalid clients %s' % clients
            if __debug__:
                for client in clients: assert isinstance(client, str), 'Invalid client value %s' % client
            identifier.clients.extend(re.compile(client) for client in clients)
            
        pattern = obj.get('Pattern')
        if pattern:
            assert isinstance(pattern, str), 'Invalid pattern %s' % pattern
            identifier.pattern = re.compile(pattern)
        
        headers = obj.get('Headers')
        if headers:
            assert isinstance(headers, list), 'Invalid headers %s' % headers
            if __debug__:
                for header in headers: assert isinstance(header, str), 'Invalid header value %s' % header
            identifier.headers.extend(re.compile(header) for header in headers)
        
        methods = obj.get('Methods')
        if methods:
            assert isinstance(methods, list), 'Invalid methods %s' % methods
            if __debug__:
                for method in methods: assert isinstance(method, str), 'Invalid method value %s' % method
            identifier.methods.update(method.upper() for method in methods)
            
        errors = obj.get('Errors')
        if errors:
            assert isinstance(errors, list), 'Invalid errors %s' % errors
            for error in errors:
                try: identifier.errors.add(int(error))
                except ValueError: raise ValueError('Invalid error value \'%s\'' % error)
        
        gateway = identifier.gateway
        assert isinstance(gateway, GatewayRepository), 'Invalid gateway %s' % gateway
        
        gateway.filters = obj.get('Filters')
        if __debug__ and gateway.filters:
            assert isinstance(gateway.filters, list), 'Invalid filters %s' % gateway.filters
            for item in gateway.filters: assert isinstance(item, str), 'Invalid filter value %s' % item
                
#        gateway.host = obj.get('Host')
#        assert not gateway.host or isinstance(gateway.host, str), 'Invalid host %s' % gateway.host
#        
#        gateway.protocol = obj.get('Protocol')
#        assert not gateway.protocol or isinstance(gateway.protocol, str), 'Invalid protocol %s' % gateway.protocol
        
        gateway.navigate = obj.get('Navigate')
        assert not gateway.navigate or isinstance(gateway.navigate, str), 'Invalid navigate %s' % gateway.navigate
        
        putHeaders = obj.get('PutHeaders')
        if putHeaders:
            assert isinstance(putHeaders, list), 'Invalid put headers %s' % putHeaders
            if __debug__:
                for putHeader in putHeaders:
                    assert isinstance(putHeader, str), 'Invalid put header value %s' % putHeader
                    assert len(putHeader.split(':')), 'Invalid put header value %s' % putHeader
            gateway.putHeaders = [putHeader.split(':', 1) for putHeader in putHeaders]
        
        return identifier
        
# --------------------------------------------------------------------

class Identifier:
    '''
    Class that maps the gateway identifier.
    '''
    __slots__ = ('gateway', 'clients', 'pattern', 'headers', 'errors', 'methods')
    
    def __init__(self, gateway):
        '''
        Construct the identifier for the provided gateway.
        
        @param gateway: GatewayRepository
            The gateway for the identifier.
        '''
        assert isinstance(gateway, GatewayRepository), 'Invalid gateway %s' % gateway
        self.gateway = gateway
        
        self.clients = []
        self.pattern = None
        self.headers = []
        self.errors = set()
        self.methods = set()

class Repository(IRepository):
    '''
    The gateways repository.
    '''
    __slots__ = ('_clientIP', '_identifiers', '_Match')
    
    def __init__(self, clientIP, identifiers, Match):
        '''
        Construct the gateways repository based on the provided dictionary object.
        
        @param identifiers: list[Identifier]
            The identifiers to be used by the repository.
        '''
        assert isinstance(clientIP, str), 'Invalid client IP %s' % clientIP
        assert isinstance(identifiers, list), 'Invalid identifiers %s' % identifiers
        assert issubclass(Match, MatchRepository), 'Invalid match class %s' % Match
        
        self._clientIP = clientIP
        self._identifiers = identifiers
        self._Match = Match
        
    def find(self, method=None, headers=None, uri=None, error=None):
        '''
        @see: IRepository.find
        '''
        for identifier in self._identifiers:
            assert isinstance(identifier, Identifier), 'Invalid identifier %s' % identifier
            
            if identifier.clients:
                for client in identifier.clients:
                    if client.match(self._clientIP): break
                else: return
                
            groupsURI = self._macth(identifier, method, headers, uri, error)
            if groupsURI is not None: return self._Match(gateway=identifier.gateway, groupsURI=groupsURI)
        
    def allowsFor(self, headers=None, uri=None):
        '''
        @see: IRepository.allowsFor
        '''
        allowed = set()
        for identifier in self._identifiers:
            assert isinstance(identifier, Identifier), 'Invalid identifier %s' % identifier
            groupsURI = self._macth(identifier, None, headers, uri, None)
            if groupsURI is not None: allowed.update(identifier.methods)
        # We need to remove auxiliar methods
        allowed.discard(HTTP_OPTIONS)
        return allowed

    # ----------------------------------------------------------------
    
    def _macth(self, identifier, method, headers, uri, error):
        '''
        Checks the match for the provided identifier and parameters.
        
        @return: tuple(string)|None
            The URI match groups, None if there is no match.
        '''
        assert isinstance(identifier, Identifier)
        groupsURI = ()
        
        if method is not None:
            assert isinstance(method, str), 'Invalid method %s' % method
            if identifier.methods:
                if method.upper() not in identifier.methods: return
        
        if headers is not None:
            assert isinstance(headers, dict), 'Invalid headers %s' % uri
            isOk = False
            if identifier.headers:
                for nameValue in headers.items():
                    header = '%s:%s' % nameValue
                    for pattern in identifier.headers:
                        if pattern.match(header):
                            isOk = True
                            break
                    if isOk: break
                if not isOk: return
        elif identifier.headers: return
                
        if uri is not None:
            assert isinstance(uri, str), 'Invalid URI %s' % uri
            if identifier.pattern:
                matcher = identifier.pattern.match(uri)
                if matcher: groupsURI = matcher.groups()
                else: return
        elif identifier.pattern: return
                
        if error is not None:
            assert isinstance(error, int), 'Invalid error %s' % error
            if identifier.errors:
                if error not in identifier.errors: return
            else: return
        elif identifier.errors: return
            
        return groupsURI
