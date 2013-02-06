'''
Created on Feb 5, 2013

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the IoC (Inversion of Control or dependency injection) events base notifications.
'''

from ..support.util_sys import callerLocals
from ._impl._setup import SetupEventControlled, register
from .error import SetupError
from .ioc import process
from .spec.trigger import Trigger
from ally.container._impl._entity import Advent
from collections import Iterable
from functools import update_wrapper
from inspect import getargspec

# --------------------------------------------------------------------

REPAIR = Trigger('repair')
# Trigger used for controlled event setup functions that repair the application.

# --------------------------------------------------------------------

def on(*triggers, priority=0):
    '''
    Decorator for setup functions that need to be executed as controlled events, used also for defining an event on entity
    function member. The detection is made based on the 'self' argument, if 'self' is found as an argument on the first 
    position then it means the event is for a function member, otherwise is for a setup function.
    
    @param triggers: arguments[ITrigger]
        The trigger(s) to be considered for calling the setup function.
    @param priority: integer
        The priority to associate with the event, a bigger number means that the event will be called earlier.
    '''
    return onDecorator(triggers, priority, callerLocals())

# --------------------------------------------------------------------

def onDecorator(triggers, priority, registry):
    '''
    Used for creating the decorator function.
    
    @param triggers: Iterable(ITrigger)
        The trigger(s) to be considered for the decorator.
    @param priority: integer
        The priority for the event.
    @param registry: dictionary{string, object}
        The registry to be used by the decorator.
    '''
    assert isinstance(triggers, Iterable), 'Invalid triggers %s' % triggers
    assert isinstance(priority, int), 'Invalid priority %s' % priority
    assert isinstance(registry, dict), 'Invalid registry %s' % registry
    
    def decorator(function):
        args = getargspec(function).args
        if args and args[0] == 'self':
            Advent.adventFor(registry).addEvent(function.__name__, priority, triggers)
            return function
        hasType, type = process(function)
        if hasType: raise SetupError('No return annotation expected for function %s' % function)
        return update_wrapper(register(SetupEventControlled(function, priority, triggers), registry), function)
    return decorator
