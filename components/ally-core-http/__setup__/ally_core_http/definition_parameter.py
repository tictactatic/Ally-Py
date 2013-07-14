'''
Created on Jul 14, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the parameters definitions.
'''

from ..ally_core.definition import addDescriber, definitionError, addError
from ..ally_core.definition_slice import updateDescribersForSlice
from ally.api.criteria import AsLike
from ally.api.option import Slice, SliceAndTotal
from ally.container import ioc
from ally.core.http.spec.codes import PARAMETER_ILLEGAL
from ally.core.http.spec.transform.encdec import CATEGORY_PARAMETER
from ally.core.impl.processor.decoder.order import OrderDecode
from ally.core.impl.verifier import VerifyCategory, VerifyName, VerifyType, \
    VerifyProperty, VerifyInfo
from ally.support.api.util_service import isCompatible

# --------------------------------------------------------------------

INFO_CRITERIA_MAIN = 'criteria_main'
# The index for main criteria info.

# --------------------------------------------------------------------

@ioc.before(definitionError)
def updateDefinitionErrorForParameters():
    addError(PARAMETER_ILLEGAL.code, VerifyCategory(CATEGORY_PARAMETER))

@ioc.before(updateDescribersForSlice)
def updateDescribersForParameters():
    # This is based on @see: updateAssemblyDecodeParameters().
    addDescriber(VerifyName(OrderDecode.nameAsc, category=CATEGORY_PARAMETER),
                 'provide the names that you want to order by ascending',
                 'the order in which the names are provided establishes the order priority')
    addDescriber(VerifyName(OrderDecode.nameDesc, category=CATEGORY_PARAMETER),
                 'provide the names that you want to order by descending',
                 'the order in which the names are provided establishes the order priority')
    
    addDescriber(VerifyType(Slice.offset, check=isCompatible),
                 'indicates the start offset in a collection from where to retrieve')
    addDescriber(VerifyType(Slice.limit, check=isCompatible),
                 'indicates the number of entities to be retrieved from a collection')
    addDescriber(VerifyType(SliceAndTotal.withTotal, check=isCompatible),
                 'indicates that the total count of the collection has to be provided')
                         
    addDescriber(VerifyProperty(AsLike.like),
                 'filters the results in a like search',
                 'you can use %% for unknown characters')
    addDescriber(VerifyProperty(AsLike.ilike),
                 'filters the results in a case insensitive like search',
                 'you can use %% for unknown characters')
                         
    addDescriber(VerifyInfo(INFO_CRITERIA_MAIN),
                 'will automatically set the value to %(' + INFO_CRITERIA_MAIN + ')s')
