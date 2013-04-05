'''
Created on Jan 5, 2012

@package: service assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl - 3.0.txt
@author: Mugur Rus

Provides the processors setups for assemblage.
'''

from ..ally_http.processor import contentLengthEncode, internalError, \
    headerEncodeResponse, headerDecodeRequest
from ally.assemblage.http.impl.processor.assembler import AssemblerHandler
from ally.assemblage.http.impl.processor.main_request import MainRequestHandler
from ally.assemblage.http.impl.processor.node import RequestedNodeHandler
from ally.container import ioc
from ally.container.error import ConfigError
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.assemblage.http.impl.processor.index import IndexProviderHandler

# --------------------------------------------------------------------

ASSEMBLAGE_INTERNAL = 'internal'
# The internal assemblage name
ASSEMBLAGE_EXTERNAL = 'external'
# The external assemblage name

# --------------------------------------------------------------------

@ioc.config
def external_host() -> str:
    ''' The external host name, something like 'localhost' '''
    raise ConfigError('No external host provided')

@ioc.config
def external_port():
    ''' The external server port'''
    return 80

@ioc.config
def assemblage_uri() -> str:
    ''' The assemblage URI to fetch the assemblage resources objects from'''
    raise ConfigError('There is no assemblage URI provided')

@ioc.config
def server_provide_assemblage():
    '''
    Indicates that this server should provide the assemblage service, possible values are:
    "internal" - the assemblage should be configured for using internal REST resources, this means that the
                 ally core http component is present in python path.
    "external" - the assemblage will use an external REST resources server, you need to configure the external host and port
                 in order to make this work.
    "don't"    - if this or any other unknown value is provided then the server will not provide assemblage service.
    '''
    return ASSEMBLAGE_INTERNAL

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.entity
def requestedNode() -> Handler: return RequestedNodeHandler()

@ioc.entity
def mainRequest() -> Handler:
    b = MainRequestHandler()
    b.assembly = assemblyForward()
    return b

@ioc.entity
def indexProvider() -> Handler: return IndexProviderHandler()

@ioc.entity
def assembler() -> Handler:
    b = AssemblerHandler()
    b.assembly = assemblyForwardInner()
    return b

# --------------------------------------------------------------------

@ioc.entity
def assemblyForward() -> Assembly:
    '''
    The assembly containing the handlers that will be used for forwarding the request.
    '''
    return Assembly('Assemblage forward')

@ioc.entity
def assemblyForwardInner() -> Assembly:
    '''
    The assembly containing the handlers that will be used for forwarding the inner requests.
    '''
    return Assembly('Assemblage inner forward')

@ioc.entity
def assemblyAssemblage() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing the assemblages resources.
    '''
    return Assembly('Assemblage resources')

# --------------------------------------------------------------------
    
@ioc.before(assemblyAssemblage)
def updateAssemblyAssemblage():
    assemblyAssemblage().add(internalError(), headerDecodeRequest(), requestedNode(), mainRequest(), indexProvider(),
                             assembler())
                             # headerEncodeResponse(), contentLengthEncode())
