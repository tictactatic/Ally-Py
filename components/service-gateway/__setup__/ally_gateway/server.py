'''
Created on Feb 1, 2013

@package: service CDM
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server configuration.
'''

from ..ally_http.server import assemblyServer, updateAssemblyServer, \
    notFoundRouter
from .processor import assemblyGateway, assemblyRequest
from ally.container import ioc
from ally.design.processor import Handler
from ally.http.impl.processor.router_by_path import RoutingByPathHandler

# --------------------------------------------------------------------

@ioc.config
def server_provide_gateway():
    ''' Flag indicating that this server should provide the gateway service'''
    return True

@ioc.config
def server_pattern_gateway():
    ''' The pattern used for matching the gateway paths in HTTP URL's'''
    return '(^resources)\/my((?=/|(?=\\.)|$).*)'

# --------------------------------------------------------------------

@ioc.entity
def gatewayRouter() -> Handler:
    b = RoutingByPathHandler()
    b.name = 'Gateway'
    b.assembly = assemblyGateway()
    b.pattern = server_pattern_gateway()
    return b

# --------------------------------------------------------------------

@ioc.before(assemblyRequest)
def updateAssemblyRequest():
    assemblyRequest().add(notFoundRouter())

@ioc.before(updateAssemblyServer)
def updateAssemblyServerForGateway():
    if server_provide_gateway(): assemblyServer().add(gatewayRouter())
