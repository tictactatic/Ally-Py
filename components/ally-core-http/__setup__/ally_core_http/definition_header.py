'''
Created on Jul 14, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the headers definitions.
'''

from ..ally_core.definition import definitions, defin, error, descriptions, desc, \
    categories, category
from ..ally_core.parsing_rendering import contentTypes
from .definition_parameter import updateErrorsForParameters
from .processor import allow_method_override, parametersAsHeaders, \
    read_from_params
from ally.api.type import typeFor
from ally.container import ioc
from ally.core.http.spec.codes import PARAMETER_ILLEGAL
from ally.core.impl.definition import Name, Category
from ally.core.spec.codes import ENCODING_UNKNOWN
from ally.http.impl.processor.method_override import METHOD_OVERRIDE
from ally.http.spec.codes import HEADER_ERROR
from ally.http.spec.headers import ACCEPT, CONTENT_TYPE

# --------------------------------------------------------------------

CATEGORY_HEADER = 'header'
# The category header.

VERIFY_CATEGORY = Category(CATEGORY_HEADER)
VERIFY_ACCEPT = Name(ACCEPT.name) & VERIFY_CATEGORY
VERIFY_CONTENT_TYPE = Name(CONTENT_TYPE.name) & VERIFY_CATEGORY

# --------------------------------------------------------------------

@ioc.entity
def parameterHeaderVerifier():
    return Name(*parametersAsHeaders()) & VERIFY_CATEGORY

# --------------------------------------------------------------------

@ioc.before(categories)
def updateCategoriesForHeaders():
    category(CATEGORY_HEADER, 'Headers')
    
@ioc.before(definitions)
def updateDefinitionsForHeaders():
    defin(category=CATEGORY_HEADER, name=ACCEPT.name, type=typeFor(str), enumeration=list(contentTypes()))
    defin(category=CATEGORY_HEADER, name=CONTENT_TYPE.name, type=typeFor(str))
    
    if allow_method_override():
        defin(category=CATEGORY_HEADER, name=METHOD_OVERRIDE.name, type=typeFor(str))
        
@ioc.after(updateErrorsForParameters)
def updateErrorsForHeaders():
    error(HEADER_ERROR.code, VERIFY_CATEGORY, 'The available headers')
    error(ENCODING_UNKNOWN.code, VERIFY_ACCEPT | VERIFY_CONTENT_TYPE, 'The content type headers')
    if read_from_params():
        error(PARAMETER_ILLEGAL.code, parameterHeaderVerifier(), 'The headers that can be provided as parameters')
    
@ioc.before(descriptions)
def updateDescriptionsForHeaders():
    desc(VERIFY_ACCEPT,
         'the accepted encodings, based on http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html',
         'the simple mime types (the ones with no slash) can be provided as URL extension')
    desc(VERIFY_CONTENT_TYPE,
         'same as \'%(name)s\' header but is to provide the input content encoding', name=ACCEPT.name)
        
    if allow_method_override():
        desc(Name(METHOD_OVERRIDE.name) & VERIFY_CATEGORY,
             'used in order to override the actual HTTP method to the specified method')
    
    if read_from_params():
        desc(parameterHeaderVerifier(),
             'the header value can also be provided as a parameter')

