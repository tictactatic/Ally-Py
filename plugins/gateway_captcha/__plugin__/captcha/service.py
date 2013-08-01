'''
Created on Jan 9, 2012

@package: captcha
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for captcha gateway.
'''
    
from ..plugin.registry import registerService
from .acl import captcha
from acl.core.impl.processor.static_right import RegisterStaticRights
from ally.container import ioc, support
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

SERVICES = 'gateway.captcha.api.**.I*Service'

support.createEntitySetup('gateway.captcha.impl.**.*')
support.listenToEntities(SERVICES, listeners=registerService)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

@ioc.entity
def registerCaptchaRight() -> Handler:
    b = RegisterStaticRights()
    b.rights = [captcha()]
    return b

# --------------------------------------------------------------------

@ioc.entity
def assemblyCaptchaGateways() -> Assembly:
    ''' The assembly used for generating reCAPTCHA gateways'''
    return Assembly('Captcha gateways')

# --------------------------------------------------------------------

@ioc.before(assemblyCaptchaGateways)
def updateAssemblyCaptchaGateways():
    assemblyCaptchaGateways().add(registerCaptchaRight())
