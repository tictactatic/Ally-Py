'''
Created on Feb 7, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the processors used in presenting REST errors.
'''

from ..ally_core.processor import renderer
from ..ally_http.processor import header, contentTypeEncode, contentLengthEncode, \
    allowEncode, methodOverride
from .processor import allow_method_override, internalDevelError, uri, \
    explainError, acceptDecode
from ally.container import ioc
from ally.core.http.impl.processor.error_populator import ErrorPopulator
from ally.design.processor import Assembly, Handler
from ally.http.spec.codes import METHOD_NOT_AVAILABLE

# --------------------------------------------------------------------

@ioc.entity
def statusToCode():
    return {
            METHOD_NOT_AVAILABLE.status: METHOD_NOT_AVAILABLE
            }

@ioc.entity
def errorPopulator() -> Handler:
    b = ErrorPopulator()
    b.statusToCode = statusToCode()
    return b

# --------------------------------------------------------------------

@ioc.entity
def assemblyErrorDelivery() -> Assembly:
    '''
    The assembly containing the handlers that will be used in delivery for the error responses.
    '''
    return Assembly()

# --------------------------------------------------------------------
    
@ioc.before(assemblyErrorDelivery)
def updateAssemblyErrorDelivery():
    assemblyErrorDelivery().add(internalDevelError(), header(), uri(), acceptDecode(),
                                renderer(), errorPopulator(), explainError(),
                                contentTypeEncode(), contentLengthEncode(), allowEncode())
    if allow_method_override(): assemblyErrorDelivery().add(methodOverride(), before=acceptDecode())
