'''
Created on Sep 13, 2012

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the no cache headers support for browsers like IE.
'''

from .processor import assemblyResources, updateAssemblyResources
from .processor_error import assemblyErrorDelivery
from .support_ajax import updateAssemblyErrorForHTTPAjax, \
    updateAssemblyResourcesForHTTPAjax
from ally.container import ioc
from ally.design.processor.handler import Handler
from ally.http.impl.processor.headers.set_fixed import HeadersSetHandler

# --------------------------------------------------------------------

@ioc.config
def no_cache() -> bool:
    '''Indicates that the server should send headers indicating that no cache is available (for browsers like IE)'''
    return True

@ioc.config
def headers_no_cache() -> dict:
    '''The headers required by browsers like IE so it will not use caching'''
    return {
            'Cache-Control':['no-cache'],
            'Pragma':['no-cache'],
            }

# --------------------------------------------------------------------

@ioc.entity
def headerSetNoCache() -> Handler:
    b = HeadersSetHandler()
    b.headers = headers_no_cache()
    return b

# --------------------------------------------------------------------

@ioc.after(updateAssemblyResources)
def updateAssemblyResourcesForHTTPNoCache():
    if no_cache(): assemblyResources().add(headerSetNoCache())

@ioc.after(updateAssemblyErrorForHTTPAjax)
def updateAssemblyErrorForHTTPNoCache():
    if no_cache(): assemblyErrorDelivery().add(headerSetNoCache(), after=headerEncodeResponse())