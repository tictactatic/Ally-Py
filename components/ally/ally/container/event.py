'''
Created on Feb 5, 2013

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the IoC (Inversion of Control or dependency injection) events base notifications.
'''

from . import ioc
from ..support.util_sys import callerLocals
from ._impl._entity import Advent
from ._impl._setup import SetupEventControlled, register
from .error import SetupError
from .impl.priority import Priority
from collections import Iterable
from functools import update_wrapper
from inspect import getargspec
import abc

# --------------------------------------------------------------------

class ITrigger(metaclass=abc.ABCMeta):
    '''
    The event trigger specification.
    '''
    
    @abc.abstractmethod
    def isTriggered(self, triggers):
        '''
        Checks if the trigger is valid for the provided triggers.
        
        @param triggers: Iterable(object)
            The triggers to check against this trigger.
        @return: boolean
            True if the trigger is valid for the provided triggers objects, False otherwise.
        '''
    
    @abc.abstractmethod
    def __hash__(self):
        '''
        The trigger hash.
        '''
        
    @abc.abstractmethod
    def __eq__(self, other):
        '''
        The trigger equal method.
        '''

class Trigger(ITrigger):
    '''
    Implementation for a @see: ITrigger that is based on the instance unicity, basically check the same object.
    The trigger can optionally wrap other triggers.
    '''
    
    def __init__(self, name, *triggers):
        '''
        Construct the composite trigger.
        
        @param name: string
            A name for the trigger.
        @param triggers: arguments[ITrigger]
            The triggers to be used by the composite trigger.
        '''
        if __debug__:
            for trigger in triggers: assert isinstance(trigger, ITrigger), 'Invalid trigger %s' % trigger
        
        self.name = name
        self.triggers = frozenset(triggers)
    
    def isTriggered(self, triggers):
        '''
        @see: ITrigger.isTriggered
        '''
        for trigger in triggers:
            if trigger is self: return True
        for trigger in self.triggers:
            assert isinstance(trigger, ITrigger), 'Invalid trigger %s' % trigger
            if trigger.isTriggered(triggers): return True
        return False
    
    def __hash__(self):
        '''
        @see: ITrigger.__hash__
        '''
        return id(self)
    
    def __eq__(self, other):
        '''
        @see: ITrigger.__eq__
        '''
        return self is other
    
# --------------------------------------------------------------------

REPAIR = Trigger('repair')
# Trigger used for controlled event setup functions that repair the application.

# --------------------------------------------------------------------

def on(*triggers, priority=ioc.PRIORITY_NORMAL):
    '''
    Decorator for setup functions that need to be executed as controlled events, used also for defining an event on entity
    function member. The detection is made based on the 'self' argument, if 'self' is found as an argument on the first 
    position then it means the event is for a function member, otherwise is for a setup function.
    
    @param triggers: arguments[ITrigger]
        The trigger(s) to be considered for calling the setup function.
    @param priority: Priority
        The priority to associate with the event.
    '''
    return onDecorator(triggers, priority, callerLocals())

# --------------------------------------------------------------------

def onDecorator(triggers, priority, registry):
    '''
    Used for creating the decorator function.
    
    @param triggers: Iterable(ITrigger)
        The trigger(s) to be considered for the decorator.
    @param priority: Priority
        The priority to associate with the event.
    @param registry: dictionary{string, object}
        The registry to be used by the decorator.
    '''
    assert isinstance(triggers, Iterable), 'Invalid triggers %s' % triggers
    assert isinstance(priority, Priority), 'Invalid priority %s' % priority
    assert isinstance(registry, dict), 'Invalid registry %s' % registry
    
    def decorator(function):
        args = getargspec(function).args
        if args and args[0] == 'self':
            Advent.adventFor(registry).addEvent(function.__name__, priority, triggers)
            return function
        hasType, type = ioc.process(function)
        if hasType: raise SetupError('No return annotation expected for function %s' % function)
        
        return update_wrapper(register(SetupEventControlled(function, priority, triggers), registry), function)
    return decorator
