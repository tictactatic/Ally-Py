'''
Created on Jun 16, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the decode processors.
'''

from ..ally_core.decode import assemblyDecode, primitiveDecode, \
    updateAssemblyDecodeForContent, describers
from ..ally_core.resources import updateDescribersForHandlers
from ally.api.criteria import AsLike
from ally.api.option import Slice, SliceAndTotal
from ally.container import ioc
from ally.core.http.spec.transform.encdec import CATEGORY_PARAMETER,\
    SEPARATOR_PARAMETERS
from ally.core.impl.processor.decoder.categorize import CategorizeHandler
from ally.core.impl.processor.decoder.option import OptionParameterDecode
from ally.core.impl.processor.decoder.order import OrderDecode
from ally.core.impl.processor.decoder.primitive_list_explode import \
    PrimitiveListExplodeDecode
from ally.core.impl.processor.decoder.query import QueryDecode, \
    INFO_CRITERIA_MAIN
from ally.core.spec.transform.describer import VerifyInfo, VerifyType, \
    VerifyProperty, VerifyName
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.support.api.util_service import isCompatible

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

@ioc.before(updateDescribersForHandlers)
def updateDescribersForParameters():
    describers().extend([
                         (VerifyName(OrderDecode.nameAsc, category=CATEGORY_PARAMETER),
                         'provide the names that you want to order by ascending',
                         'the order in which the names are provided establishes the order priority'),
                         (VerifyName(OrderDecode.nameDesc, category=CATEGORY_PARAMETER),
                         'provide the names that you want to order by descending',
                         'the order in which the names are provided establishes the order priority'),
                         
                         (VerifyType(Slice.offset, check=isCompatible),
                         'indicates the start offset in a collection from where to retrieve'),
                         (VerifyType(Slice.limit, check=isCompatible),
                         'indicates the number of entities to be retrieved from a collection'),
                         (VerifyType(SliceAndTotal.withTotal, check=isCompatible),
                         'indicates that the total count of the collection has to be provided'),
                         
                         (VerifyProperty(AsLike.like),
                         'filters the results in a like search',
                         'you can use %% for unknown characters'),
                         (VerifyProperty(AsLike.ilike),
                         'filters the results in a case insensitive like search',
                         'you can use %% for unknown characters'),
                         
                         (VerifyInfo(INFO_CRITERIA_MAIN),
                         'will automatically set the value to %(' + INFO_CRITERIA_MAIN + ')s')
                         ])
