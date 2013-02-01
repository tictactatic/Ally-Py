'''
Created on Jan 12, 2012

@package: ally core plugin
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup registry for the plugins.
'''

from __setup__.ally_core.resources import resourcesRegister
from ally.container.proxy import proxyWrapFor
from functools import partial

# --------------------------------------------------------------------

def registerService(service, binders=None):
    '''
    A listener to register the service.
    
    @param service: object
        The service to be registered.
    @param binders: list[Callable]|tuple(Callable)
        The binders used for the registered services.
    '''
    proxy = proxyWrapFor(service)
    if binders:
        for binder in binders: binder(proxy)
    resourcesRegister().register(proxy)

def addService(*binders):
    '''
    Create listener to register the service with the provided binders.
    
    @param binders: arguments[Callable]
        The binders used for the registered services.
    '''
    return partial(registerService, binders=binders)

