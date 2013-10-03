'''
Created on Oct 2, 2013

@package: ally distribution
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the services setup for getting API data.
'''

from ally.container import ioc
from ally.container.error import SetupError
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.http.impl.processor.forward import ForwardHTTPHandler
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@ioc.config
def external_host() -> str:
    ''' The external host name, something like 'localhost' '''
    return 'localhost'

@ioc.config
def external_port():
    ''' The external server port'''
    return 8080

# --------------------------------------------------------------------

@ioc.entity
def assemblyRESTRequest() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing the REST requests.
    '''
    return Assembly('REST data')

# --------------------------------------------------------------------

try:
    from ally.http.impl.processor.headers.accept import AcceptRequestEncodeHandler
    from ally.http.impl.processor.headers.content_length import \
        ContentLengthDecodeHandler
    from ally.support.http.request import RequesterGetJSON
except ImportError:
    log.warn('No HTTP core available, services that require API data will not be available because of this.')
    
    @ioc.entity
    def requesterGetJSON(): raise SetupError('Not available without the ally-http component')
    
else:
    
    @ioc.entity
    def acceptRequestEncode() -> Handler: return AcceptRequestEncodeHandler()
    
    @ioc.entity
    def contentLengthDecode() -> Handler: return ContentLengthDecodeHandler()
    
    @ioc.entity
    def externalForward() -> Handler:
        b = ForwardHTTPHandler()
        b.externalHost = external_host()
        b.externalPort = external_port()
        return b
    
    @ioc.entity
    def requesterGetJSON() -> RequesterGetJSON: return RequesterGetJSON(assemblyRESTRequest())
    
    # --------------------------------------------------------------------
    
    @ioc.before(assemblyRESTRequest)
    def updateAssemblyRESTRequestForExternal():
        assemblyRESTRequest().add(acceptRequestEncode(), contentLengthDecode(), externalForward())
