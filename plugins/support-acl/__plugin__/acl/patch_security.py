'''
Created on Feb 22, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the security plugin support patches.
'''

from ally.container import support
import logging


# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from .. import security
except ImportError: log.info('No security plugin available, thus no need to register synchronizers')
else:
    security = security  # Just to avoid the import warning
    # ----------------------------------------------------------------
    
    from acl.core.impl.synchronizer import SynchronizerRights
    support.createEntitySetup(SynchronizerRights)
