'''
Created on Jul 14, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content definitions.
'''

from .definition import descriptions, desc, categories, category
from .parsing_rendering import CATEGORY_CONTENT_XML, CATEGORY_CONTENT_OBJECT
from ally.container import ioc
from ally.core.impl.definition import ModelId


# --------------------------------------------------------------------

@ioc.before(categories)
def updateCategoriesForContent():
    category(CATEGORY_CONTENT_XML, 'XML content xpaths')
    category(CATEGORY_CONTENT_OBJECT, 'Object content properties')

@ioc.before(descriptions)
def updateDescriptionsForContent():
    desc(ModelId(), 'represents the model id')  # This is based on @see: modelDecode()
    # TODO: Gabriel: Add more content definitions

