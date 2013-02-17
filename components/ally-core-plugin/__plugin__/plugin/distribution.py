'''
Created on Feb 6, 2013

@package: ally core plugin
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the distribution controlled events for the plugins.
'''

from __setup__.ally_core_plugin.distribution import distribution_file_path, \
    application_mode, APP_DEVEL
from ally.container import ioc, support, app
from ally.container.config import load, save, Config
from os.path import isfile
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@ioc.entity
def markers():
    ''' The markers for the executed events'''
    markers = {}
    if isfile(distribution_file_path()):
        with open(distribution_file_path(), 'r') as f:
            for key, value in load(f).items(): markers['__plugin__.%s' % key] = value
    return markers

# --------------------------------------------------------------------

@ioc.start(priority= -1)  # The lowest priority
def deploy():
    try:
        for name, call in support.eventsFor(app.DEPLOY):
            log.debug('Executing deploy event call \'%s\'', name)
            call()
        
        for name, call in support.eventsFor(app.POPULATE):
            executed = markers().get(name)
            if executed is None:
                executed = call()
                log.debug('Executed populate event call \'%s\' for the first time and got %s', name, executed)
            elif not executed:
                executed = call()
                log.debug('Executed populate event call \'%s\' again and got %s', name, executed)
            else:
                log.debug('No need to execute populate event call \'%s\'', name)
            markers()[name] = executed
            
        if application_mode() == APP_DEVEL:
            for name, call in support.eventsFor(app.DEVEL):
                executed = call()
                log.debug('Executed development event call \'%s\' and got %s', name, executed)
                markers()[name] = executed
    finally:
        plen = len('__plugin__.')
        with open(distribution_file_path(), 'w') as f:
            save({name[plen:]: Config(name, value) for name, value in markers().items()}, f)
