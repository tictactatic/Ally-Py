'''
Created on Nov 23, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Runs the basic web server.
'''

from .processor import assemblyNotFound, connectionClose, connection
from ally.container import ioc
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler, RoutingHandler
from ally.http.server import server_basic
from threading import Thread

# --------------------------------------------------------------------

SERVER_BASIC = 'basic'
# The basic server name

# --------------------------------------------------------------------
# The default configurations

@ioc.config
def server_type() -> str:
    '''
    The type of the server to use, the options are:
    "basic"- single threaded server, the safest but slowest server to use.
    '''
    return SERVER_BASIC

@ioc.config
def server_protocol() -> str:
    '''
    The HTTP protocol to be used for the server.
    '''
    return 'HTTP/1.1'

@ioc.config
def server_host() -> str:
    '''The IP address to bind the server to, something like 127.0.0.1'''
    return '0.0.0.0'

@ioc.config
def server_port() -> int:
    '''The port on which the server will run'''
    return 8080

@ioc.config
def server_version() -> str:
    '''The server version name'''
    return 'Ally/0.1'

# --------------------------------------------------------------------

@ioc.entity
def assemblyServer() -> Assembly:
    '''
    The assembly used in processing the server requests.
    '''
    return Assembly('Server')

# --------------------------------------------------------------------

@ioc.entity
def serverBasicRequestHandler():
    return type('RequestHandler', (server_basic.RequestHandler,), {'protocol_version': server_protocol()})

@ioc.entity
def serverBasic():
    b = server_basic.BasicServer()
    b.serverVersion = server_version()
    b.serverHost = server_host()
    b.serverPort = server_port()
    b.requestHandlerFactory = serverBasicRequestHandler()
    b.assembly = assemblyServer()
    return b

# --------------------------------------------------------------------

@ioc.entity
def notFoundRouter() -> Handler: return RoutingHandler(assemblyNotFound())

# --------------------------------------------------------------------

@ioc.before(assemblyServer)
def updateAssemblyServerForProtocolSupport():
    if server_protocol() >= 'HTTP/1.1':
        if server_type() == 'basic': assemblyServer().add(connectionClose())
        # For the basic version we don't need the ensure length because is closing the connection anyway.
        else: assemblyServer().add(connection())
    
@ioc.after(updateAssemblyServerForProtocolSupport)
def updateAssemblyServer():
    assemblyServer().add(notFoundRouter())

# --------------------------------------------------------------------

@ioc.start
def runServer():
    if server_type() == 'basic':
        Thread(name='HTTP server thread', target=server_basic.run, args=(serverBasic(),)).start()
