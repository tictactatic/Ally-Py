'''
Created on Feb 5, 2013

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the event trigger specification and basic implementations.
'''

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

# --------------------------------------------------------------------

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
    
