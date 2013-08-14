'''
Created on Aug 14, 2013

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds Gateway objects based on database GatewayData.
'''

from ally.container.support import setup
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.support.api.util_service import copyContainer
from ally.support.sqlalchemy.session import SessionSupport
from collections import Iterable
from gateway.api.gateway import Gateway
from gateway.meta.gateway import GatewayData
import itertools
import json

# --------------------------------------------------------------------

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    gateways = defines(Iterable, doc='''
    @rtype: Iterable(Gateway)
    The default gateways.
    ''')

# --------------------------------------------------------------------

@setup(Handler, name='databaseGateways')
class DatabaseGatewaysAlchemy(HandlerProcessor, SessionSupport):
    '''
    Provides the handler that populates Gateway objects based on database GatewayData.
    '''
    
    def process(self, chain, reply:Reply, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the databse gateways.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        
        gateways = []
        for data in self.session().query(GatewayData).all():
            assert isinstance(data, GatewayData), 'Invalid data %s' % data

            gatewayData = json.loads(str(data.identifier, 'utf8'))
            gatewayData.update(json.loads(str(data.navigate, 'utf8')))
            gateways.append(copyContainer(gatewayData, Gateway()))

        if reply.gateways is not None: reply.gateways = itertools.chain(reply.gateways, gateways)
        else: reply.gateways = gateways

