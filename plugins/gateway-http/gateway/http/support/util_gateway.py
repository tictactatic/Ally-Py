'''
Created on Feb 18, 2013

@package: gateway http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Utility functions related to gateways.
'''

from gateway.http.api.gateway import Gateway

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
    for key in ('Pattern', 'Headers', 'Methods', 'Filters', 'Errors', 'Host', 'Protocol', 'Navigate'):
        value = config.get(key)
        if value is not None:
            if __debug__:
                if key == 'Pattern': assert isinstance(value, str), 'Invalid Pattern %s' % value
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
                    
            setattr(gateway, key, value)
            assert keys.add(key) or True
            
    assert len(keys) == len(config), 'Invalid gateway configuration names: %s' % (', '.join(keys.difference(config)))
    return gateway
