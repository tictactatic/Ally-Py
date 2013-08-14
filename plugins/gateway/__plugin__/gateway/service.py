'''
Created on Jan 9, 2012

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for gateway.
'''
    
from ..plugin.registry import registerService
from .db_gateway import bindGatewaySession
from ally.container import support, ioc, bind, app
from ally.design.processor.assembly import Assembly
import re
from ally.container.support import entityFor
from gateway.api.gateway import IGatewayService, Gateway
import logging
from ally.support.api.util_service import copyContainer

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

asPattern = lambda rootURI: '^%s(?:/|(?=\\.)|$)(.*)' % re.escape(rootURI)
# Make the root URI into a gateway pattern.

# --------------------------------------------------------------------

databaseGateways = gatewayMethodMerge = registerMethodOverride = support.notCreated  # Just to avoid errors

SERVICES = 'gateway.api.**.I*Service'
@ioc.entity
def binders(): return [bindGatewaySession]

bind.bindToEntities('gateway.impl.**.*Alchemy', binders=binders)
support.createEntitySetup('gateway.impl.**.*', 'gateway.core.impl.**.*')
support.listenToEntities(SERVICES, listeners=registerService, beforeBinding=False)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

@ioc.entity
def assemblyAnonymousGateways() -> Assembly:
    ''' The assembly used for generating anonymous gateways'''
    return Assembly('Anonymous gateways')

# --------------------------------------------------------------------

@ioc.entity
def defaultGateways() -> list: return []

# --------------------------------------------------------------------

@ioc.before(assemblyAnonymousGateways)
def updateAssemblyAnonymousGateways():
    assemblyAnonymousGateways().add(databaseGateways(), gatewayMethodMerge(), registerMethodOverride())

@app.populate(app.DEVEL, app.CHANGED)
def populateDefaulyGateways():
    serviceGateway = entityFor(IGatewayService)
    assert isinstance(serviceGateway, IGatewayService)
    
    for data in defaultGateways():
        try: serviceGateway.insert(copyContainer(data, Gateway()))
        except: log.info('Gateway %s already exists' % data)


# TODO: Gabriel: see command line for plugins.
#
# @ioc.config
# def full_access_ips():
#    '''
#    A list that contains the IPs that have full unrestricted access to the REST server.
#    The IP can be provided as: 127.0.0.1 or 127.*.*.*
#    '''
#    return []
#
## --------------------------------------------------------------------
# @ioc.before(default_gateways)
# def updateDefaultGatewaysForFullAccess():
#    ips = []
#    for ip in full_access_ips():
#        ip = '\.'.join(mark.replace('*', '\d+') for mark in ip.split('.'))
#        ips.append(ip)
#    if ips:
#        default_gateways().append({
#                                   'Clients': ips,
#                                   'Pattern': '(.*)',
#                                   })
