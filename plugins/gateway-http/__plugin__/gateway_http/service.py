'''
Created on Jan 9, 2012

@package: gateway http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for http gateway.
'''
    
from ..plugin.registry import registerService
from __setup__.ally_core_http.processor_error import statusToCode
from __setup__.ally_core_http.server import server_pattern_resources, \
    server_pattern_errors
from ally.container import support, ioc
from ally.container.support import nameInEntity
from ally.http.spec.codes import METHOD_NOT_AVAILABLE, PATH_NOT_FOUND, \
    UNAUTHORIZED_ACCESS, FORBIDDEN_ACCESS
from gateway.http.impl.gateway import GatewayService

# --------------------------------------------------------------------

SERVICES = 'gateway.http.api.**.I*Service'

support.createEntitySetup('gateway.http.impl.**.*')
support.listenToEntities(SERVICES, listeners=registerService)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

default_gateways = ioc.entityOf(nameInEntity(GatewayService, 'default_gateways'))

# --------------------------------------------------------------------

@ioc.before(statusToCode)
def updateStatusToCodeForGateway():
    statusToCode().update({
                           UNAUTHORIZED_ACCESS.status: UNAUTHORIZED_ACCESS,
                           FORBIDDEN_ACCESS.status: FORBIDDEN_ACCESS,
                           })

ioc.doc(server_pattern_errors, '''
!Attention if you change this configuration you need also to adjust the 'default_gateways' configuration
''')

@ioc.before(default_gateways)
def updateGatewayWithResourcesErrors():
    default_gateways().extend([
                               # If path is not found then we try to dispatch a unauthorized access if the path is not found
                               # in REST the default error will have priority over the unauthorized access
                               {
                                'Pattern': server_pattern_resources(),
                                'Errors': [PATH_NOT_FOUND.status],
                                'Navigate': 'error/{1}?status=%s' % UNAUTHORIZED_ACCESS.status,
                                },
                               {
                                'Pattern': server_pattern_resources(),
                                'Errors': [FORBIDDEN_ACCESS.status, METHOD_NOT_AVAILABLE.status],
                                'Navigate': 'error/{1}',
                                },
                               ])
