'''
Created on Nov 24, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the processors for handling OPTIONS requests.
'''

from .processor import updateAssemblyGateway, assemblyGateway, headersCustom, \
    parametersAsHeaders, read_from_params, gatewayForward
from ally.container import ioc
from ally.design.processor.handler import Handler
from ally.http.impl.processor.cors import CrossOriginResourceSharingHandler
from ally.http.spec.headers import ALLOW_HEADERS, PARAMETERS_AS_HEADERS

# --------------------------------------------------------------------

@ioc.config
def allow_origin() -> list:
    '''The allow origin to dispatch for responses'''
    return ['*']

# --------------------------------------------------------------------


@ioc.entity
def crossOriginOthersOptions() -> dict:
    return {
            ALLOW_HEADERS: sorted(headersCustom()),
            }

@ioc.entity
def crossOriginResourceSharing() -> Handler:
    b = CrossOriginResourceSharingHandler()
    b.allowOrigin = allow_origin()
    b.othersOptions = crossOriginOthersOptions()
    return b

# --------------------------------------------------------------------

@ioc.before(crossOriginOthersOptions)
def updateCrossOriginOthersOptionsForParams():
    if read_from_params():
        crossOriginOthersOptions()[PARAMETERS_AS_HEADERS] = parametersAsHeaders()

@ioc.after(updateAssemblyGateway)
def updateAssemblyGatewayForCors():
    assemblyGateway().add(crossOriginResourceSharing(), after=gatewayForward())
