'''
Created on Jan 10, 2013

@package: ally plugin
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the IoC container plugin distribution support.
'''

from .event import REPAIR, onDecorator, Trigger, ITrigger
from ally.design.priority import PRIORITY_NORMAL #@UnusedImport
from ally.support.util_sys import callerLocals
from itertools import chain

# --------------------------------------------------------------------

REPAIR = REPAIR
SETUP = Trigger('setup')
# Trigger used for controlled event setup that is called in order to provide component setup.

DEPLOY = Trigger('deploy') 
# Trigger used for controlled event setup that is called on application deploy.
POPULATE = Trigger('populate')
# Trigger used for controlled event setup that is called on application populate.
CHANGED = Trigger('changed', REPAIR)
# Event used for controlled event setup that is called when the application distribution changes.

SUPPORT = Trigger('support')
# Event used for controlled event setup that is called when the application is in support mode.
NORMAL = Trigger('normal')
# Event used for controlled event setup that is called when the application is in normal mode.
DEVEL = Trigger('development', CHANGED)
# Event used for controlled event setup that is called when the application is in development mode.

# --------------------------------------------------------------------

def setup(*triggers, priority=PRIORITY_NORMAL):
    '''
    Decorator for conditional setup functions that need to be called for components setups. The setup function will be called 
    until a True or None value is returned. This should manly be used in order to patch component setup only one time.
    If the function returns False it means it needs to be called again for the same event, if True or None is returned
    it means the function executed successfully.
    
    @param triggers: arguments[ITrigger]
        Additional triggers to be considered for the patch, this events will trigger the patch for other situations
        rather just the application first start.
    @param priority: one of priority markers
        The priority to associate with the event.
    '''
    if not triggers: return onDecorator((POPULATE, SETUP), priority, callerLocals())
    if len(triggers) == 1 and not isinstance(triggers[0], ITrigger):
        return onDecorator((POPULATE, SETUP), priority, callerLocals())(triggers[0])
    return onDecorator(chain(triggers, (POPULATE, SETUP)), priority, callerLocals())

# --------------------------------------------------------------------

def deploy(*triggers, priority=PRIORITY_NORMAL):
    '''
    Decorator for deploy setup functions. The deploy function will be called every time the application is started.
    This should manly be used to gather data.
    
    @param triggers: arguments[ITrigger]
        Triggers to be considered for the deploy call, this will actually condition the deploy call to the provided triggers.
    @param priority: one of priority markers
        The priority to associate with the event.
    '''
    if not triggers: return onDecorator((DEPLOY,), priority, callerLocals())
    if len(triggers) == 1 and not isinstance(triggers[0], ITrigger):
        return onDecorator((DEPLOY,), priority, callerLocals())(triggers[0])
    return onDecorator(triggers, priority, callerLocals())

def populate(*triggers, priority=PRIORITY_NORMAL):
    '''
    Decorator for populate setup functions. The populate function will be called until a True or None value is returned.
    This should manly be used in order to populate default data.
    If the function returns False it means it needs to be called again for the same event, if True or None is returned
    it means the function executed successfully.
    
    @param triggers: arguments[ITrigger]
        Additional triggers to be considered for the populate, this events will trigger the populate for other situations
        rather just the application first start.
    @param priority: one of priority markers
        The priority to associate with the event.
    '''
    if not triggers: return onDecorator((POPULATE,), priority, callerLocals())
    if len(triggers) == 1 and not isinstance(triggers[0], ITrigger):
        return onDecorator((POPULATE,), priority, callerLocals())(triggers[0])
    return onDecorator(chain(triggers, (POPULATE,)), priority, callerLocals())
