'''
Created on Nov 24, 2011

@package: service CDM
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the Cross-Origin Resource Sharing setup required by browser.
'''

from .processor import updateAssemblyContent, assemblyContent, contentDelivery
from ally.container import ioc
from ally.design.processor.handler import Handler
from ally.http.impl.processor.cors import CrossOriginResourceSharingHandler
from ally.http.impl.processor.method_deliver_ok import DeliverOkForMethodHandler
from ally.http.spec.server import HTTP_OPTIONS, HTTP_GET

# --------------------------------------------------------------------

@ioc.config
def allow_origin() -> list:
    '''The allow origin to dispatch for responses'''
    return ['*']

@ioc.config
def allow_methods() -> list:
    '''The allow methods to dispatch for OPTIONS'''
    return [HTTP_GET]

# --------------------------------------------------------------------

@ioc.entity
def crossOriginResourceSharing() -> Handler:
    b = CrossOriginResourceSharingHandler()
    b.allowOrigin = allow_origin()
    b.allowMethods = allow_methods()
    return b

@ioc.entity
def deliverOkForOptionsHandler() -> Handler:
    b = DeliverOkForMethodHandler()
    b.forMethod = HTTP_OPTIONS
    return b

# --------------------------------------------------------------------

@ioc.after(updateAssemblyContent)
def updateAssemblyContentOptions():
    assemblyContent().add(crossOriginResourceSharing(), deliverOkForOptionsHandler(), before=contentDelivery())
