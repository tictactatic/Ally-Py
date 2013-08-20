'''
Created on Feb 6, 2013

@package: ally plugin
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the distribution controlled events for the plugins.
'''

from ally.container import ioc, app, support
from ally.container.event import ITrigger
from ally.container.impl.config import load, save, Config
from ally.design.priority import Priority, PRIORITY_LAST
from os.path import isfile
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

PRIORITY_PERSIST_MARKERS = Priority('Persist events markers', before=PRIORITY_LAST)
# The persist markers priority.

APP_NORMAL = 'normal'
# Name used for normal application mode.
APP_DEVEL = 'devel'
# Name used for development application mode.

# --------------------------------------------------------------------

@ioc.config
def distribution_file_path():
    ''' The name of the distribution file for the plugins deployments'''
    return 'distribution.properties'

@ioc.config
def application_mode():
    '''
    The distribution application mode, the possible values are:
    "normal" - the application behaves as the normal production instance, this means:
            * the deployments are executed every time, as it should normally would
            * the populates are executed only once as it should normally would

    "devel" - the application behaves as a development instance, this means:
            * the deployments are executed every time, as it should normally would
            * the populates are executed only once as it should normally would except those that are marked for development.
    '''
    return APP_DEVEL

# --------------------------------------------------------------------

@ioc.entity
def markers():
    ''' The markers for the executed events'''
    markers = {}
    if isfile(distribution_file_path()):
        with open(distribution_file_path(), 'r') as f:
            for key, value in load(f).items(): markers['__plugin__.%s' % key] = value
    return markers

@ioc.entity
def used():
    ''' The used markers'''
    return set()
    
# --------------------------------------------------------------------

@ioc.start(priority=PRIORITY_PERSIST_MARKERS)
def persistMarkers():
    ''' Persist the markers of the executed events'''
    plen = len('__plugin__.')
    configs = {}
    for name, value in markers().items():
        assert name.startswith('__plugin__.'), 'Invalid name \'%s\' is not from a plugin' % name
        if name in used(): group = 'current markers'
        else: group = 'unused markers'
        configs[name[plen:]] = Config(name, value, group)
    with open(distribution_file_path(), 'w') as f: save(configs, f)

# --------------------------------------------------------------------

def triggerEvents(*triggers, always=(app.DEPLOY,), regardless=(app.DEVEL,), otherwise=(app.NORMAL, app.DEVEL)):
    '''
    Triggers the event for the provided triggers in accordance with the plugin distribution.
    The defaults of this function are for normal application execution.
    
    @param triggers: arguments[object]
        The triggers to perform the events for.
    @param always: tuple(ITrigger)
        The triggers that if present should always be executed.
    @param regardless: tuple(ITrigger)
        The triggers that if present with POPULATE should always be executed.
    @param otherwise: tuple(ITrigger)
        The triggers that if no POPULATE is present should otherwise be executed.
    '''
    assert triggers, 'At least one trigger is required'
    assert isinstance(always, tuple), 'Invalid always triggers %s' % always
    assert isinstance(regardless, tuple), 'Invalid regardless triggers %s' % regardless
    assert isinstance(otherwise, tuple), 'Invalid otherwise triggers %s' % otherwise
    if __debug__:
        for trigger in always: assert isinstance(trigger, ITrigger), 'Invalid always trigger %s' % trigger
        for trigger in regardless: assert isinstance(trigger, ITrigger), 'Invalid regardless trigger %s' % trigger
        for trigger in otherwise: assert isinstance(trigger, ITrigger), 'Invalid otherwise trigger %s' % trigger
    
    for call, name, ctriggers in support.eventsFor(*triggers):
        if app.DEVEL.isTriggered(ctriggers) and application_mode() != APP_DEVEL: continue
        if app.NORMAL.isTriggered(ctriggers) and application_mode() != APP_NORMAL: continue
        
        if any(trigger.isTriggered(ctriggers) for trigger in always):
            log.debug('Executing always event call \'%s\'', name)
            call()
        elif app.POPULATE.isTriggered(ctriggers):
            used().add(name)
            executed = markers().get(name)
            if any(trigger.isTriggered(ctriggers) for trigger in regardless): executed = None
            if executed is None:
                executed = call()
                log.debug('Executed populate event call \'%s\' for the first time and got %s', name, executed)
            elif not executed:
                executed = call()
                log.debug('Executed populate event call \'%s\' again and got %s', name, executed)
            else:
                log.debug('No need to execute populate event call \'%s\'', name)
            markers()[name] = executed

        elif any(trigger.isTriggered(ctriggers) for trigger in otherwise):
            log.debug('Executing otherwise event call \'%s\'', name)
            call()
