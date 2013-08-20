'''
Created on Feb 6, 2013

@package: ally plugin
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the controlled events deploy for the plugins setup.
'''

from __setup__.ally_plugin.distribution import triggerEvents
from ally.container import ioc, app
from ally.design.priority import PRIORITY_LAST, Priority

# --------------------------------------------------------------------

PRIORITY_DEPLOY = Priority('Deploy plugin setup', before=PRIORITY_LAST)
# The deploy priority.

# --------------------------------------------------------------------

@ioc.start(priority=PRIORITY_DEPLOY)
def deployEvents():
    triggerEvents(app.SETUP)
