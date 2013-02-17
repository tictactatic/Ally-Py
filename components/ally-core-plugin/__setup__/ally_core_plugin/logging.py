'''
Created on Nov 7, 2012

@package: ally core plugin
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Update the default logging.
'''

from ..ally.logging import info_for
from .distribution import application_mode, APP_DEVEL
from ally.container import ioc
from ally.design import processor
import __plugin__
import logging

# --------------------------------------------------------------------

@ioc.before(info_for)
def updateInfos():
    info_for().append(__plugin__.__name__)

# --------------------------------------------------------------------

@ioc.start(priority=10)
def updateDevelopment():
    if application_mode() == APP_DEVEL:
        logging.getLogger(processor.__name__).setLevel(logging.INFO)
