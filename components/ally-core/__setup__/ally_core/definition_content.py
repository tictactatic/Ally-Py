'''
Created on Jul 14, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content definitions.
'''

from datetime import datetime

from ally.api.type import typeFor
from ally.container import ioc
from ally.core.impl.definition import ModelId, PropertyType

from ..ally_core.processor import converter
from .definition import descriptions, desc, categories, category
from .parsing_rendering import CATEGORY_CONTENT_XML, CATEGORY_CONTENT_OBJECT


# --------------------------------------------------------------------
@ioc.before(categories)
def updateCategoriesForContent():
    category(CATEGORY_CONTENT_XML, 'XML content xpaths')
    category(CATEGORY_CONTENT_OBJECT, 'Object content properties')

@ioc.before(descriptions)
def updateDescriptionsForContent():
    desc(ModelId(), 'represents the model id') # This is based on @see: modelDecode()
    desc(PropertyType(datetime), 'example %(sample)s', sample=converter().asString(datetime(1982, 1, 18, 2, 40, 12), typeFor(datetime)))

    # TODO: Gabriel: Add more content definitions

