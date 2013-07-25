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
from .decode import CATEGORY_PARAMETER
from ally.api.criteria import AsLike
from ally.api.operator.type import TypeCriteria
from ally.container import ioc
from ally.core.http.impl.processor.decoder.create_parameter_order import \
    NAME_ASC, NAME_DESC
from ally.core.http.spec.codes import PARAMETER_ILLEGAL
from ally.core.impl.definition import Category, Name, Property, ReferencesNames, \
    PropertyTypeOf

# --------------------------------------------------------------------

VERIFY_CATEGORY = Category(CATEGORY_PARAMETER)

# --------------------------------------------------------------------

@ioc.before(categories)
def updateCategoriesForParameters():
    category(CATEGORY_PARAMETER, 'Parameters')
    
@ioc.before(errors)
def updateErrorsForParameters():
    error(PARAMETER_ILLEGAL.code, VERIFY_CATEGORY, 'The available parameters for this URL')

@ioc.before(descriptions)
def updateDescriptionsForParameters():
    # This is based on @see: updateAssemblyDecodeParameters().
    desc(Name(NAME_ASC) & VERIFY_CATEGORY,
         'provide the names that you want to order by ascending',
         'the order in which the names are provided establishes the order priority')
    desc(Name(NAME_DESC) & VERIFY_CATEGORY,
         'provide the names that you want to order by descending',
         'the order in which the names are provided establishes the order priority')
                         
    desc(Property(AsLike.like),
         'filters the results in a like search',
         'you can use %% for unknown characters')
    desc(Property(AsLike.ilike),
         'filters the results in a case insensitive like search',
         'you can use %% for unknown characters')

    desc(PropertyTypeOf(TypeCriteria) & VERIFY_CATEGORY,
         'will automatically set the value to %(properties)s', properties=ReferencesNames())
