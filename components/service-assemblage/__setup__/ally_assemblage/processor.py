'''
Created on Jan 5, 2012

@package: service assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl - 3.0.txt
@author: Gabriel Nistor

Provides the processors setups for assemblage.
'''

from ..ally_http.processor import chunkedTransferEncoding, \
    contentTypeResponseDecode, internalError, acceptRequestEncode, \
    contentLengthDecode
from ..ally_http.server import notFoundRouter, server_protocol
from ally.assemblage.http.impl.processor.assembler import AssemblerHandler
from ally.assemblage.http.impl.processor.block import BlockHandler
from ally.assemblage.http.impl.processor.content import ContentHandler
from ally.assemblage.http.impl.processor.index import IndexProviderHandler
from ally.assemblage.http.impl.processor.node import RequestNodeHandler, \
    ASSEMBLAGE
from ally.container import ioc
from ally.container.error import SetupError
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler, RenamerHandler
from ally.http.impl.processor.forward import ForwardHTTPHandler
from ally.http.impl.processor.header_parameter import HeaderParameterHandler, \
    HeaderParameterOptionsHandler
from ally.http.impl.processor.method_override import METHOD_OVERRIDE
from ally.http.spec.headers import CONTENT_LENGTH
from ally.indexing.impl import perform_do
from ally.support.http.request import RequesterOptions, RequesterGetJSON

# --------------------------------------------------------------------

ASSEMBLAGE_INTERNAL = 'internal'
# The internal assemblage name
ASSEMBLAGE_EXTERNAL = 'external'
# The external assemblage name

# --------------------------------------------------------------------

@ioc.config
def external_host() -> str:
    ''' The external host name, something like 'localhost' '''
    return 'localhost'

@ioc.config
def external_port():
    ''' The external server port'''
    return 8081

@ioc.config
def external_rest_host() -> str:
    ''' The external host name for REST resources, something like 'localhost' '''
    return 'localhost'

@ioc.config
def external_rest_port():
    ''' The external server port for REST resources'''
    return 8082

@ioc.config
def assemblage_indexes_uri() -> str:
    ''' The block indexes URI to fetch the index block objects from, the place holder '%s' is replaced with the block id'''
    return 'resources/Indexing/Block/%s'

@ioc.config
def default_response_charset() -> str:
    '''The default response character set to use if none is provided in the request'''
    return 'ISO-8859-1'

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

@ioc.config
def read_from_params():
    '''If true will allow the assemblage proxy server to read the assemblage headers also from parameters.'''
    return True

@ioc.config
def inner_headers_remove() -> list:
    '''
    The headers to be removed from the inner requests.
    '''
    return [METHOD_OVERRIDE.name, CONTENT_LENGTH.name]

# --------------------------------------------------------------------

@ioc.entity
def assemblyRESTRequest() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing the assemblage REST requests.
    '''
    return Assembly('Assemblage REST data')

@ioc.entity
def assemblyForward() -> Assembly:
    '''
    The assembly containing the handlers that will be used for forwarding the request.
    '''
    return Assembly('Assemblage forward')

@ioc.entity
def assemblyContent() -> Assembly:
    '''
    The assembly containing the handlers that will be used for processing the assemblage content.
    '''
    return Assembly('Assemblage content')

@ioc.entity
def assemblyAssemblage() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing the assemblages resources.
    '''
    return Assembly('Assemblage')

# --------------------------------------------------------------------

@ioc.entity
def headersCustom() -> set:
    '''
    Provides the custom header names defined by processors.
    '''
    return set()

@ioc.entity
def parametersAsHeaders() -> list: return sorted(headersCustom())

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.entity
def requesterForwardOptions() -> RequesterOptions: return RequesterOptions(assemblyForward())

@ioc.entity
def requesterRESTGetJSON() -> RequesterGetJSON: return RequesterGetJSON(assemblyRESTRequest())

@ioc.entity
def headerParameter() -> Handler:
    b = HeaderParameterHandler()
    b.parameters = parametersAsHeaders()
    return b

@ioc.entity
def headerParameterOptions() -> Handler:
    b = HeaderParameterOptionsHandler()
    b.requesterOptions = requesterForwardOptions()
    return b

@ioc.entity
def requestNode(): return RequestNodeHandler()

@ioc.entity
def block() -> Handler:
    b = BlockHandler()
    b.uri = assemblage_indexes_uri()
    b.requesterGetJSON = requesterRESTGetJSON()
    return b

@ioc.entity
def content() -> Handler:
    b = ContentHandler()
    b.assemblyForward = assemblyForward()
    b.assemblyContent = assemblyContent()
    b.charSetDefault = default_response_charset()
    b.innerHeadersRemove = inner_headers_remove()
    return b

@ioc.entity
def indexProvider() -> Handler: return IndexProviderHandler()

@ioc.entity
def encodingProvider() -> Handler:
    return RenamerHandler(contentTypeResponseDecode(), 'response', ('responseCnt', 'content'))

@ioc.entity
def assembler() -> Handler:
    b = AssemblerHandler()
    b.doProcessors = perform_do.processors
    return b

@ioc.entity
def externalForward() -> Handler:
    b = ForwardHTTPHandler()
    b.externalHost = external_host()
    b.externalPort = external_port()
    return b

@ioc.entity
def externalForwardREST() -> Handler:
    b = ForwardHTTPHandler()
    b.externalHost = external_rest_host()
    b.externalPort = external_rest_port()
    return b

# --------------------------------------------------------------------

@ioc.before(headersCustom)
def updateHeadersCustom():
    headersCustom().add(ASSEMBLAGE.name)
    
@ioc.before(assemblyAssemblage)
def updateAssemblyAssemblage():
    if not server_protocol() >= 'HTTP/1.1':
        raise SetupError('Invalid protocol %s for chunk transfer is available only '
                         'for HTTP/1.1 protocol or greater' % server_protocol())
    assemblyAssemblage().add(internalError(), block(), requestNode(), headerParameterOptions(), content(), assembler(),
                             chunkedTransferEncoding())
    if read_from_params(): assemblyAssemblage().add(headerParameter(), after=internalError())
    
@ioc.before(assemblyContent)
def updateAssemblyContent():
    assemblyContent().add(indexProvider(), encodingProvider())
    
@ioc.before(assemblyForward)
def updateAssemblyForward():
    if server_provide_assemblage() == ASSEMBLAGE_EXTERNAL:
        assemblyForward().add(contentLengthDecode(), externalForward())
    else: assemblyForward().add(notFoundRouter())
    
@ioc.before(assemblyRESTRequest)
def updateAssemblyRESTRequestForExternal():
    if server_provide_assemblage() == ASSEMBLAGE_EXTERNAL:
        assemblyRESTRequest().add(acceptRequestEncode(), contentLengthDecode(), externalForwardREST())
            
