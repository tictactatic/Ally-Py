'''
Created on Nov 7, 2012

@package: ally plugin
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Update the default logging.
'''

from ..ally.logging import info_for
from .distribution import application_mode, APP_DEVEL
from ally.container import ioc
from ally.design import processor
from ally.design.priority import PRIORITY_FIRST, PRIORITY_LAST, sortByPriorities, \
    Priority
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@ioc.before(info_for)
def updateInfos():
    info_for().append('__plugin__')

# --------------------------------------------------------------------

@ioc.start(priority=PRIORITY_FIRST)
def updateDevelopment():
    if application_mode() == APP_DEVEL:
        logging.getLogger(processor.__name__).setLevel(logging.INFO)

@ioc.start(priority=PRIORITY_LAST)
def presentPriorities():
    if application_mode() == APP_DEVEL:
        priorities = list(PRIORITY_FIRST.group)
        sortByPriorities(priorities)
        
        st = []
        for priority in priorities:
            assert isinstance(priority, Priority), 'Invalid priority' % priority
            st.append('{0: <40s}{1:s}'.format(priority.name, priority.location))
            
        log.debug('Priorities in the defined order:\n%s', '\n'.join(st))
