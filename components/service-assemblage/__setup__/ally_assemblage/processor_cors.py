'''
Created on Nov 24, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the processors for handling Cross-Origin Resource Sharing.
'''

from .processor import parametersAsHeaders, read_from_params, headersCustom, \
    updateAssemblyAssemblage, assemblyAssemblage, content
from ally.container import ioc
from ally.design.processor.handler import Handler
from ally.http.impl.processor.cors import CrossOriginResourceSharingHandler
from ally.http.spec.headers import ALLOW_HEADERS, PARAMETERS_AS_HEADERS

# --------------------------------------------------------------------

@ioc.entity
def crossOriginOthersOptions() -> dict:
    return {
            ALLOW_HEADERS: sorted(headersCustom()),
            }

@ioc.entity
def crossOriginResourceSharing() -> Handler:
    b = CrossOriginResourceSharingHandler()
    b.othersOptions = crossOriginOthersOptions()
    return b

# --------------------------------------------------------------------

@ioc.before(crossOriginOthersOptions)
def updateCrossOriginOthersOptionsForParams():
    if read_from_params():
        crossOriginOthersOptions()[PARAMETERS_AS_HEADERS] = parametersAsHeaders()

@ioc.after(updateAssemblyAssemblage)
def updateAssemblyAssemblageForCors():
    assemblyAssemblage().add(crossOriginResourceSharing(), after=content())

