'''
Created on Feb 6, 2013

@package: ally plugin
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the distribution controlled events for the plugins.
'''

from __setup__.ally_plugin.distribution import application_mode, APP_DEVEL, \
    APP_NORMAL, markers, persistMarkers
from ally.container import ioc, support, app
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@ioc.start(priority=ioc.PRIORITY_FINAL)
def deploy():
    used = set()
    try:
        triggers = [app.DEPLOY, app.POPULATE]
        if application_mode() == APP_NORMAL: triggers.append(app.NORMAL)
        elif application_mode() == APP_DEVEL: triggers.append(app.DEVEL)

        for call, name, trigger in support.eventsFor(*triggers):
            trigger = (trigger,)
            if app.DEPLOY.isTriggered(trigger):
                log.debug('Executing event call \'%s\'', name)
                call()
            elif app.POPULATE.isTriggered(trigger):
                used.add(name)
                executed = markers().get(name)
                if app.DEVEL.isTriggered(trigger): executed = None  # If in devel then we execute regardless
                if executed is None:
                    executed = call()
                    log.debug('Executed populate event call \'%s\' for the first time and got %s', name, executed)
                elif not executed:
                    executed = call()
                    log.debug('Executed populate event call \'%s\' again and got %s', name, executed)
                else:
                    log.debug('No need to execute populate event call \'%s\'', name)
                markers()[name] = executed

            elif app.NORMAL.isTriggered(trigger):
                log.debug('Executing normal only deploy event call \'%s\'', name)
                call()
            elif app.DEVEL.isTriggered(trigger):
                log.debug('Executing development only deploy event call \'%s\'', name)
                call()
    finally: persistMarkers(used)
