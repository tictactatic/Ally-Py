'''
Created on Jan 5, 2012

@package: service CDM
@copyright: 2012 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl - 3.0.txt
@author: Mugur Rus

Provides the configurations for delivering files from the local file system.
'''

from ..ally_http.processor import internalError
from ally.container import ioc
from ally.container.error import ConfigError
from ally.design.processor import Handler, Assembly
from ally.gateway.http.impl.processor.filter import GatewayFilterHandler
from ally.gateway.http.impl.processor.forward import GatewayForwardHandler
from ally.gateway.http.impl.processor.place_error import GatewayErrorHandler
from ally.gateway.http.impl.processor.respository import \
    GatewayRepositoryHandler
from ally.gateway.http.impl.processor.selector import GatewaySelectorHandler

# --------------------------------------------------------------------

@ioc.config
def gateway_uri() -> str:
    '''
    The gateway URI to fetch the Gateway objects from'''
    raise ConfigError('There is no access URI provided')

@ioc.config
def cleanup_interval():
    ''' The anonymous gateway data cleanup interval, this is basically the interval the anonymous gateway refreshes the data'''
    return 60

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.entity
def gatewayRepository() -> Handler:
    b = GatewayRepositoryHandler()
    b.uri = gateway_uri()
    b.cleanupInterval = cleanup_interval()
    b.assembly = assemblyRequest()
    return b

@ioc.entity
def gatewaySelector() -> Handler: return GatewaySelectorHandler()

@ioc.entity
def gatewayFilter() -> Handler:
    b = GatewayFilterHandler()
    b.assembly = assemblyRequest()
    return b

@ioc.entity
def gatewayError() -> Handler: return GatewayErrorHandler()

@ioc.entity
def gatewayForward() -> Handler:
    b = GatewayForwardHandler()
    b.assembly = assemblyRequest()
    return b

# --------------------------------------------------------------------

@ioc.entity
def assemblyRequest() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing the gateway requests.
    '''
    return Assembly()

@ioc.entity
def assemblyGateway() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing the gateway.
    '''
    return Assembly()

# --------------------------------------------------------------------
    
@ioc.before(assemblyGateway)
def updateAssemblyGateway():
    assemblyGateway().add(internalError(), gatewayRepository(), gatewaySelector(), gatewayFilter(), gatewayError(),
                          gatewayForward())
    
