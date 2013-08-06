'''
Created on Feb 1, 2013

@package: service assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server configuration.
'''

from ..ally_http.server import assemblyServer, updateAssemblyServer
from .processor import ASSEMBLAGE_INTERNAL, ASSEMBLAGE_EXTERNAL, \
    server_provide_assemblage, assemblyAssemblage
from ally.container import ioc
from ally.design.processor.handler import Handler, RoutingHandler

# --------------------------------------------------------------------

@ioc.entity
def assemblageRouter() -> Handler: return RoutingHandler(assemblyAssemblage())

# --------------------------------------------------------------------

@ioc.before(updateAssemblyServer)
def updateAssemblyServerForGatewayExternal():
    if server_provide_assemblage() in (ASSEMBLAGE_INTERNAL, ASSEMBLAGE_EXTERNAL): assemblyServer().add(assemblageRouter())
