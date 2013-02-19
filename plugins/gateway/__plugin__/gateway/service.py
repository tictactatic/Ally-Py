'''
Created on Jan 9, 2012

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for gateway.
'''
    
from ..plugin.registry import registerService
from ally.container import support, ioc
from ally.container.support import nameInEntity
from gateway.impl.gateway import GatewayService

# --------------------------------------------------------------------

SERVICES = 'gateway.api.**.I*Service'

support.createEntitySetup('gateway.impl.**.*')
support.listenToEntities(SERVICES, listeners=registerService)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

default_gateways = ioc.entityOf(nameInEntity(GatewayService, 'default_gateways'))

# --------------------------------------------------------------------
