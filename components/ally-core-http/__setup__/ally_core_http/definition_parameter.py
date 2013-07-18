'''
Created on Jul 14, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the parameters definitions.
'''

from ..ally_core.definition import errors, error, descriptions, desc, categories, \
    category
from ..ally_core.definition_slice import updateDescriptionsForSlice
from ally.api.criteria import AsLike
from ally.api.operator.type import TypeCriteria
from ally.api.option import Slice, SliceAndTotal
from ally.container import ioc
from ally.core.http.impl.processor.assembler.decoding_parameter import \
    CATEGORY_PARAMETER
from ally.core.http.impl.processor.decoder.parameter.order import OrderDecode
from ally.core.http.spec.codes import PARAMETER_ILLEGAL
from ally.core.impl.definition import Category, Name, InputType, Property, \
    ReferenceNames, PropertyTypeOf
from ally.support.api.util_service import isCompatible

# --------------------------------------------------------------------

VERIFY_CATEGORY = Category(CATEGORY_PARAMETER)

# --------------------------------------------------------------------

@ioc.before(categories)
def updateCategoriesForParameters():
    category(CATEGORY_PARAMETER, 'Parameters')
    
@ioc.before(errors)
def updateErrorsForParameters():
    error(PARAMETER_ILLEGAL.code, VERIFY_CATEGORY, 'The available parameters for this URL')

@ioc.before(descriptions, updateDescriptionsForSlice)
def updateDescriptionsForParameters():
    # This is based on @see: updateAssemblyDecodeParameters().
    desc(Name(OrderDecode.nameAsc) & VERIFY_CATEGORY,
         'provide the names that you want to order by ascending',
         'the order in which the names are provided establishes the order priority')
    desc(Name(OrderDecode.nameDesc) & VERIFY_CATEGORY,
         'provide the names that you want to order by descending',
         'the order in which the names are provided establishes the order priority')
    
    desc(InputType(Slice.offset, check=isCompatible),
         'indicates the start offset in a collection from where to retrieve')
    desc(InputType(Slice.limit, check=isCompatible),
         'indicates the number of entities to be retrieved from a collection')
    desc(InputType(SliceAndTotal.withTotal, check=isCompatible),
         'indicates that the total count of the collection has to be provided')
                         
    desc(Property(AsLike.like),
         'filters the results in a like search',
         'you can use %% for unknown characters')
    desc(Property(AsLike.ilike),
         'filters the results in a case insensitive like search',
         'you can use %% for unknown characters')

    desc(PropertyTypeOf(TypeCriteria) & VERIFY_CATEGORY,
         'will automatically set the value to %(properties)s', properties=ReferenceNames())
