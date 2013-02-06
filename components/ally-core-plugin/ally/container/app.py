'''
Created on Jan 10, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the IoC container plugin distribution support.
'''

from .spec.trigger import Trigger
from ally.container.event import REPAIR, onDecorator
from ally.container.spec.trigger import ITrigger
from ally.support.util_sys import callerLocals
from itertools import chain

# --------------------------------------------------------------------

REPAIR = REPAIR
DEPLOY = Trigger('deploy') 
# Trigger used for controlled event setup that is called on application deploy.
POPULATE = Trigger('populate')
# Trigger used for controlled event setup that is called on application populate.

CHANGED = Trigger('changed', REPAIR)
# Event used for controlled event setup that is called when the application distribution changes.
DEVEL = Trigger('development')
# Event used for controlled event setup that is called when the application is in development mode.

# --------------------------------------------------------------------

def deploy(*args, priority=0):
    '''
    Decorator for deploy setup functions. The deploy function will be called every time the  application is started.
    This should manly be used to gather data.
    
    @param priority: integer
        The priority to associate with the event, a bigger number means that the event will be called earlier.
    '''
    decorator = onDecorator((DEPLOY,), priority, callerLocals())
    if not args: return decorator
    assert len(args) == 1, 'Expected only one argument that is the decorator function, got %s arguments' % len(args)
    return decorator(args[0])

def populate(*triggers, priority=0):
    '''
    Decorator for populate setup functions. The populate function will be called until a True or None value is returned.
    This should manly be used in order to populate default data.
    If the function returns False it means it needs to be called again for the same event, if True or None is returned
    it means the function executed successfully.
    
    @param triggers: arguments[ITrigger]
        Additional triggers to be considered for the populate, this events will trigger the populate for other situations
        rather just the application first start.
    @param priority: integer
        The priority to associate with the event, a bigger number means that the event will be called earlier.
    '''
    if not triggers: return onDecorator((POPULATE,), callerLocals())
    if len(triggers) == 1 and not isinstance(triggers[0], ITrigger):
        return onDecorator((POPULATE,), priority, callerLocals())(triggers[0])
    return onDecorator(chain(triggers, (POPULATE,)), priority, callerLocals())
