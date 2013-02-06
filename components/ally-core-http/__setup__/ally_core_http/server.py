'''
Created on Feb 1, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server configuration.
'''

from ..ally.logging import info_for
from ..ally_http.server import updateAssemblyServer, assemblyServer
from .processor import assemblyResources
from ally.container import ioc
from ally.design.processor import Handler
from ally.http.impl.processor.router_by_path import RoutingByPathHandler

# --------------------------------------------------------------------

@ioc.config
def server_provide_rest() -> bool:
    ''' Flag indicating that this server should provide REST resources'''
    return True

@ioc.config
def server_pattern_rest():
    '''
    The pattern used for matching the REST resources paths in HTTP URL's
    !Attention if this is changed you also need to adjust the 'resources_root_uri' configuration to have properly rendered
    references
    '''
    return '^resources(?:/|(?=\\.)|$)(.*)'

# --------------------------------------------------------------------

@ioc.entity
def resourcesRouter() -> Handler:
    b = RoutingByPathHandler()
    b.name = 'REST resources'
    b.assembly = assemblyResources()
    b.pattern = server_pattern_rest()
    return b
    
@ioc.before(updateAssemblyServer)
def updateAssemblyServerForResources():
    if server_provide_rest(): assemblyServer().add(resourcesRouter())
    
@ioc.before(info_for)
def updateLoggingForResourcesServer():
    info_for().append('ally.http.impl.processor.router_by_path')
    
