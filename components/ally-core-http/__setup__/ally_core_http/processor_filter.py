'''
Created on Aug 23, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the processors used in resolving input filters.
'''

from ..ally_http.server import notFoundRouter
from .processor import assemblyResources, parsing
from .server import root_uri_resources
from ally.container import ioc
from ally.core.http.impl.processor.filter_input import FilterInputHandler
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.http.impl.processor.router_by_path import RoutingByPathHandler
from ally.support.http.request import RequesterGetJSON

# --------------------------------------------------------------------

@ioc.entity
def assemblyRESTRequest() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing the filter REST requests.
    '''
    return Assembly('Filter REST data')

@ioc.entity
def assemblyRESTInternal() -> Assembly:
    '''
    The assembly containing the handlers that will be used for internally processing REST resources.
    '''
    return Assembly('Filter REST resources')

# --------------------------------------------------------------------

@ioc.entity
def filterRequesterGetJSON() -> RequesterGetJSON:
    return RequesterGetJSON(assemblyRESTRequest())

@ioc.entity
def resourcesRouterInternal() -> Handler:
    b = RoutingByPathHandler()
    b.assembly = assemblyRESTInternal()
    b.rootURI = root_uri_resources()
    return b

@ioc.entity
def filterInput() -> Handler:
    b = FilterInputHandler()
    b.requesterGetJSON = filterRequesterGetJSON()
    return b

# --------------------------------------------------------------------

@ioc.before(assemblyRESTRequest)
def updateAssemblyRESTRequest():
    assemblyRESTRequest().add(resourcesRouterInternal(), notFoundRouter())
    
@ioc.after(assemblyResources)
def updateAssemblyResourcesForFilter():
    assemblyRESTInternal().add(assemblyResources())
    assemblyResources().add(filterInput(), after=parsing())
