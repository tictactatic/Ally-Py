'''
Created on Feb 1, 2013

@package: service CDM
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server configuration.
'''

from ..ally_http.server import assemblyServer, updateAssemblyServer
from .processor import assemblyGateway, server_provide_gateway, GATEWAY_EXTERNAL
from ally.container import ioc
from ally.design.processor.handler import Handler
from ally.http.impl.processor.router_by_path import RoutingByPathHandler

# --------------------------------------------------------------------

@ioc.config
def server_pattern_gateway():
    ''' The pattern used for matching the gateway paths in HTTP URL's'''
    return '(^resources)\/my((?=/|(?=\\.)|$).*)'

# --------------------------------------------------------------------

@ioc.entity
def gatewayRouter() -> Handler:
    b = RoutingByPathHandler()
    b.assembly = assemblyGateway()
    b.pattern = server_pattern_gateway()
    return b

# --------------------------------------------------------------------

@ioc.before(updateAssemblyServer)
def updateAssemblyServerForGatewayExternal():
    if server_provide_gateway() == GATEWAY_EXTERNAL:
        assemblyServer().add(gatewayRouter())
