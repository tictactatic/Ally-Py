'''
Created on Jun 16, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the decode processors.
'''

from ..ally_core.decode import assemblyDecode, primitiveDecode, \
    updateAssemblyDecodeForContent
from .definition_parameter import INFO_CRITERIA_MAIN
from ally.container import ioc
from ally.core.http.spec.transform.encdec import CATEGORY_PARAMETER, \
    SEPARATOR_PARAMETERS
from ally.core.impl.processor.decoder.categorize import CategorizeHandler
from ally.core.impl.processor.decoder.option import OptionParameterDecode
from ally.core.impl.processor.decoder.order import OrderDecode
from ally.core.impl.processor.decoder.primitive_list_explode import \
    PrimitiveListExplodeDecode
from ally.core.impl.processor.decoder.query import QueryDecode
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

@ioc.entity
def assemblyDecodeParameters() -> Assembly:
    '''
    The assembly containing the decoders for parameters.
    '''
    return Assembly('Decode parameters')

@ioc.entity
def assemblyDecodeOrder() -> Assembly:
    '''
    The assembly containing the decoders for query order parameters.
    '''
    return Assembly('Decode parameters order')

# --------------------------------------------------------------------

@ioc.entity
def categoryParameters() -> Handler:
    b = CategorizeHandler()
    b.categoryAssembly = assemblyDecodeParameters()
    b.category = CATEGORY_PARAMETER
    return b

@ioc.entity
def optionParameterDecode() -> Handler: return OptionParameterDecode()

@ioc.entity
def queryDecode() -> Handler:
    b = QueryDecode()
    b.separator = SEPARATOR_PARAMETERS
    b.infoCriteriaMain = INFO_CRITERIA_MAIN
    return b

@ioc.entity
def orderDecode() -> Handler:
    b = OrderDecode()
    b.orderAssembly = assemblyDecodeOrder()
    return b

@ioc.entity
def listExplodeDecode() -> Handler: return PrimitiveListExplodeDecode()

# --------------------------------------------------------------------

@ioc.before(assemblyDecodeOrder)
def updateAssemblyDecodeOrder():
    assemblyDecodeOrder().add(primitiveDecode(), listExplodeDecode())
    
@ioc.before(assemblyDecodeParameters)
def updateAssemblyDecodeParameters():
    assemblyDecodeParameters().add(queryDecode(), orderDecode(), optionParameterDecode(), primitiveDecode(),
                                   listExplodeDecode())
    
@ioc.before(updateAssemblyDecodeForContent)
def updateAssemblyDecodeForParameters():
    assemblyDecode().add(categoryParameters())
