'''
Created on Feb 21, 2013

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds default Gateway objects.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from collections import Iterable
from gateway.api.gateway import Gateway
import itertools
from inspect import getdoc
from ally.support.api.util_service import namesFor

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

@injected
@setup(Handler, name='registerDefaultGateways')
class RegisterDefaultGateways(HandlerProcessor):
    '''
    Provides the handler that populates default gateways.
    '''
    
    default_gateways = []; wire.config('default_gateways', doc='''
    The default gateways that are available for any unauthorized access. %s
    ''' % getdoc(Gateway))
    
    def __init__(self):
        '''
        Construct the default gateways register.
        '''
        assert isinstance(self.default_gateways, list), 'Invalid default gateways %s' % self.default_gateways
        super().__init__()
        
        self._gateways = []
        for config in self.default_gateways: self._gateways.append(gatewayFrom(config))
    
    def process(self, chain, reply:Reply, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the default gateways.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply

        if reply.gateways is not None: reply.gateways = itertools.chain(self._gateways, reply.gateways)
        else: reply.gateways = self._gateways

# --------------------------------------------------------------------

def gatewayFrom(config):
    '''
    Constructs a gateway from the provided configuration dictionary.
    
    @param config: dictionary{string, ...}
        The configurations dictionary to construct the gateway based on.
    @return: Gateway
        The constructed gateway.
    '''
    assert isinstance(config, dict), 'Invalid gateway configuration %s' % config
    if __debug__: keys = set()
    gateway = Gateway()
    for key in namesFor(Gateway):
        value = config.get(key)
        if value is not None:
            if __debug__:
                if key == 'Clients':
                    assert isinstance(value, list), 'Invalid Clients %s' % value
                    for item in value: assert isinstance(item, str), 'Invalid Client value %s' % item
                elif key == 'Pattern': assert isinstance(value, str), 'Invalid Pattern %s' % value
                elif key == 'Headers':
                    assert isinstance(value, list), 'Invalid Headers %s' % value
                    for item in value: assert isinstance(item, str), 'Invalid Headers value %s' % item
                elif key == 'Methods':
                    assert isinstance(value, list), 'Invalid Methods %s' % value
                    for item in value: assert isinstance(item, str), 'Invalid Methods value %s' % item
                elif key == 'Filters':
                    assert isinstance(value, list), 'Invalid Filters %s' % value
                    for item in value: assert isinstance(item, str), 'Invalid Filters value %s' % item
                elif key == 'Errors':
                    assert isinstance(value, list), 'Invalid Errors %s' % value
                    for item in value: assert isinstance(item, int), 'Invalid Errors value %s' % item
                elif key == 'Host': assert isinstance(value, str), 'Invalid Host %s' % value
                elif key == 'Protocol': assert isinstance(value, str), 'Invalid Protocol %s' % value
                elif key == 'Navigate': assert isinstance(value, str), 'Invalid Navigate %s' % value
                elif key == 'PutHeaders':
                    assert isinstance(value, dict), 'Invalid PutHeaders %s' % value
                    for key, item in value.items():
                        assert isinstance(key, str), 'Invalid PutHeaders key %s' % key
                        assert isinstance(item, str), 'Invalid PutHeaders value %s' % item
                    
            setattr(gateway, key, value)
            assert keys.add(key) or True
            
    assert len(keys) == len(config), 'Invalid gateway configuration names: %s' % (', '.join(keys.difference(config)))
    return gateway
