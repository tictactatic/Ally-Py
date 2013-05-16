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
from ally.design.processor.attribute import defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.gateway.http.spec.gateway import IRepository, Gateway, Match
from ally.http.spec.codes import BAD_GATEWAY, CodedHTTP
from ally.support.http.util_dispatch import RequestDispatch, obtainJSON
from sched import scheduler
from threading import Thread
import time

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    repository = defines(IRepository)
    
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
    external server. The Gateway structure is defined as in the @see: gateway plugin.
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

    def process(self, chain, processing, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Obtains the repository.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        if not self._repository:
            jobj, _status, text = obtainJSON(processing, self.uri, details=True)
            if jobj is None:
                BAD_GATEWAY.set(response)
                response.text = text
                return
            self._repository = Repository(jobj)
        request.repository = self._repository

    # ----------------------------------------------------------------
    
    def initialize(self):
        '''
        Initialize the repository.
        '''
        self._repository = None
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
        self._repository = None
        
# --------------------------------------------------------------------

class Repository(IRepository):
    '''
    The gateways repository.
    '''
    __slots__ = ('_gateways', '_cache')
    
    def __init__(self, objs):
        '''
        Construct the gateways repository based on the provided dictionary object.
        
        @param objs: dictionary{string: list[dictionary{...}]}
            The dictionary used for defining the repository gateways, the objects as is defined from response.
        '''
        assert isinstance(objs, dict), 'Invalid objects %s' % objs
        assert 'GatewayList' in objs, 'Invalid objects %s, no GatewayList' % objs
        
        self._gateways = [Gateway(obj) for obj in objs['GatewayList']]
        self._cache = {}
        
    def find(self, method=None, headers=None, uri=None, error=None):
        '''
        @see: IRepository.find
        '''
        for gateway in self._gateways:
            groupsURI = self._match(gateway, method, headers, uri, error)
            if groupsURI is not None: return Match(gateway, groupsURI)
        
    def allowsFor(self, headers=None, uri=None):
        '''
        @see: IRepository.allowsFor
        '''
        allowed = set()
        for gateway in self._gateways:
            assert isinstance(gateway, Gateway)
            groupsURI = self._match(gateway, None, headers, uri, None)
            if groupsURI is not None: allowed.update(gateway.methods)
        return allowed
        
    def obtainCache(self, identifier):
        '''
        @see: IRepository.obtainCache
        '''
        cache = self._cache.get(identifier)
        if cache is None: cache = self._cache[identifier] = {}
        return cache

    # ----------------------------------------------------------------
    
    def _match(self, gateway, method, headers, uri, error):
        '''
        Checks the match for the provided gateway and parameters.
        
        @return: tuple(string)|None
            The URI match groups, None if there is no match.
        '''
        assert isinstance(gateway, Gateway)
        groupsURI = ()
        
        if method is not None:
            assert isinstance(method, str), 'Invalid method %s' % method
            if gateway.methods:
                if method.upper() not in gateway.methods: return
        
        if headers is not None:
            assert isinstance(headers, dict), 'Invalid headers %s' % uri
            isOk = False
            if gateway.headers:
                for nameValue in headers.items():
                    header = '%s:%s' % nameValue
                    for pattern in gateway.headers:
                        if pattern.match(header):
                            isOk = True
                            break
                    if isOk: break
                if not isOk: return
                
        if uri is not None:
            assert isinstance(uri, str), 'Invalid URI %s' % uri
            if gateway.pattern:
                matcher = gateway.pattern.match(uri)
                if matcher: groupsURI = matcher.groups()
                else: return
                
        if error is not None:
            assert isinstance(error, int), 'Invalid error %s' % error
            if gateway.errors:
                if error not in gateway.errors: return
            else: return
            
        return groupsURI
