'''
Created on May 14, 2013

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides application profiling.
'''

from ..ally_http.processor import contentLengthEncode
from .server import assemblyServer, updateAssemblyServer
from ally.container import ioc
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.http.impl.processor.profiler_view import ProfilerViewHandlerHandler
from ally.http.impl.processor.router_by_path import RoutingByPathHandler

# --------------------------------------------------------------------

@ioc.config
def profile_server() -> bool:
    ''' Profile the server, should only be used in development or staging, never production'''
    return False
    
# --------------------------------------------------------------------

@ioc.entity
def profiler():
    from cProfile import Profile
    return Profile()

@ioc.entity
def profilerView() -> Handler:
    b = ProfilerViewHandlerHandler()
    b.profiler = profiler()
    return b

# --------------------------------------------------------------------

@ioc.entity
def assemblyProfile() -> Assembly:
    '''
    The assembly used in processing the profile requests.
    '''
    return Assembly('Profile')

# --------------------------------------------------------------------

@ioc.entity
def profileRouter() -> Handler:
    b = RoutingByPathHandler()
    b.assembly = assemblyProfile()
    b.pattern = '^profile(?:/|(?=\\.)|$)'
    return b

# --------------------------------------------------------------------

@ioc.before(assemblyProfile)
def updateAssemblyProfile():
    assemblyProfile().add(profilerView(), contentLengthEncode())

    
@ioc.before(assemblyServer, updateAssemblyServer)
def updateAssemblyServerForProfile():
    if profile_server(): assemblyServer().add(profileRouter())

# --------------------------------------------------------------------

@ioc.start(priority=ioc.PRIORITY_TOP)
def startProfile():
    if profile_server(): profiler().enable()
