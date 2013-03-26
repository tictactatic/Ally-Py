'''
Created on Feb 1, 2013

@package: service assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server configuration.
'''

from ..ally_http.server import assemblyServer, updateAssemblyServer
from .processor import assemblyAssemblage, ASSEMBLAGE_EXTERNAL, \
    server_provide_assemblage
from ally.container import ioc
from ally.design.processor.handler import Handler
from ally.http.impl.processor.router_by_path import RoutingByPathHandler

# --------------------------------------------------------------------

@ioc.config
def server_pattern_assemblage():
    '''
    The pattern used for matching the assemblage paths in HTTP URL's
    '''
    return '(.*)'

# --------------------------------------------------------------------

@ioc.entity
def assemblageRouter() -> Handler:
    b = RoutingByPathHandler()
    b.assembly = assemblyAssemblage()
    b.pattern = server_pattern_assemblage()
    return b

# --------------------------------------------------------------------

@ioc.before(updateAssemblyServer)
def updateAssemblyServerForGatewayExternal():
    if server_provide_assemblage() == ASSEMBLAGE_EXTERNAL:
        assemblyServer().add(assemblageRouter())
