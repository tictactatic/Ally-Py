'''
Created on Jan 28, 2013

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the default anonymous gateway data.
'''

from ..api.gateway import IGatewayService, Gateway
from ..meta.gateway import GatewayData
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, FILL_ALL
from ally.support.api.util_service import namesFor
from ally.support.sqlalchemy.session import SessionSupport
from collections import Iterable
from gateway.api.gateway import GatewayIdentifier
import binascii
import json

# --------------------------------------------------------------------

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Required
    gateways = requires(Iterable, doc='''
    @rtype: Iterable(Gateway)
    The gateways.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(IGatewayService, name='gatewayService')
class GatewayServiceAlchemy(IGatewayService, SessionSupport):
    '''
    Implementation for @see: IGatewayService that provides the default anonymous gateway data.
    '''
    
    assemblyAnonymousGateways = Assembly; wire.entity('assemblyAnonymousGateways')
    # The assembly to be used for generating gateways
    
    def __init__(self):
        assert isinstance(self.assemblyAnonymousGateways, Assembly), \
        'Invalid assembly gateways %s' % self.assemblyAnonymousGateways
        
        self._processing = self.assemblyAnonymousGateways.create(reply=Reply)
         
    def getAnonymous(self):
        '''
        @see: IGatewayService.getAnonymous
        '''
        proc = self._processing
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        reply = proc.execute(FILL_ALL).reply
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        if Reply.gateways not in reply: return ()
        return reply.gateways
    
    def insert(self, gateway):
        '''
        @see: IGatewayService.insert
        '''
        hash, identifier, navigate = self.dataFor(gateway)
    
        data = GatewayData()
        data.hash = hash
        data.identifier, data.navigate = identifier.encode(), navigate.encode()
        self.session().add(data)
        self.session().flush((data,))
        return hash
    
    def update(self, gateway):
        '''
        @see: IGatewayService.update
        '''
        assert isinstance(gateway, Gateway), 'Invalid gateway %s' % gateway
        
        data = self.session().query(GatewayData).get(gateway.Hash)
        if data is None: raise InvalidIdError()
        assert isinstance(data, GatewayData), 'Invalid data %s' % data
        data.navigate = self.dataFor(gateway, onlyNavigate=True).encode()
        
    def delete(self, gatewayHash):
        '''
        @see: IGatewayService.delete
        '''
        assert isinstance(gatewayHash, str), 'Invalid gateway hash %s' % gatewayHash
        return self.session().query(GatewayData).filter(GatewayData.hash == gatewayHash).delete() > 0

    # ----------------------------------------------------------------
    
    def dataFor(self, gateway, onlyNavigate=False):
        '''
        Provides the json serialized data for the gateway.
        '''
        assert isinstance(gateway, Gateway), 'Invalid gateway %s' % gateway
        
        navigateData, namesIdentifier = {}, set(namesFor(GatewayIdentifier))
        if not onlyNavigate: identifierData = {}
        for name in namesFor(Gateway):
            if name == 'Hash': continue
            if onlyNavigate and name in namesIdentifier: continue
            
            value = getattr(gateway, name)
            if isinstance(value, list): value = sorted(value)
            if name in namesIdentifier: identifierData[name] = value
            else: navigateData[name] = value
        
        navigate = json.dumps(navigateData, sort_keys=True)
        if onlyNavigate: return navigate
        
        identifier = json.dumps(identifierData, sort_keys=True)
        hash = ('%x' % binascii.crc32(identifier.encode(), 0)).upper()
        return hash, identifier, navigate
        
