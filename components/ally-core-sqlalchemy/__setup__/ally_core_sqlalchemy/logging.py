'''
Created on Nov 7, 2012

@package: ally plugin
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Update the default logging.
'''

from ..ally_plugin.distribution import APP_DEVEL, application_mode
from ally.container import ioc
from ally.core.sqlalchemy import processor
from ally.design.priority import PRIORITY_FIRST
import logging

# --------------------------------------------------------------------

@ioc.start(priority=PRIORITY_FIRST)
def updateDevelopmentForSQLErrors():
    if application_mode() == APP_DEVEL:
        logging.getLogger(processor.__name__).setLevel(logging.INFO)

