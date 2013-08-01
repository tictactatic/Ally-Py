'''
Created on Feb 19, 2013

@package: captcha
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ally core http setup patch.
'''

from .service import assemblyCaptchaGateways
from ally.container import ioc
from ally.design.processor.handler import Handler
from ally.design.processor.processor import restructure
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from __setup__ import ally_core_http # @UnusedImport
except ImportError: log.info('No ally core http component available, thus cannot populate captcha gateway processors')
else:
    from .patch_ally_core import gatewaysFromPermissions, updateAssemblyCaptchaGatewaysForResources
    from __setup__.ally_core_http.processor import encoderPathResource
    
    # --------------------------------------------------------------------
    
    @ioc.entity
    def encoderPathGateway() -> Handler:
        return restructure(encoderPathResource(), ('response', 'solicitation'), ('request', 'solicitation'))
        
    # --------------------------------------------------------------------
        
    @ioc.after(updateAssemblyCaptchaGatewaysForResources)
    def updateAssemblyCaptchaGatewaysForHTTPResources():
        assemblyCaptchaGateways().add(encoderPathGateway(), before=gatewaysFromPermissions())
