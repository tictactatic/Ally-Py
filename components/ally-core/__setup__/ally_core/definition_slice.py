'''
Created on Jul 14, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the slice definitions.
'''

from .decode import slice_limit_default, slice_limit_maximum, slice_with_total
from .definition import desc, descriptions
from ally.api.option import Slice, SliceAndTotal
from ally.container import ioc
from ally.core.impl.definition import InputType
from ally.support.api.util_service import isCompatible

# --------------------------------------------------------------------

VERIFY_OFFSET = InputType(Slice.offset, check=isCompatible)
VERIFY_LIMIT = InputType(Slice.limit, check=isCompatible)
VERIFY_TOTAL = InputType(SliceAndTotal.withTotal, check=isCompatible)

# --------------------------------------------------------------------

@ioc.before(descriptions)
def updateDescriptionsForSlice():
    # This is based on @see:  optionSlice().
    
    desc(VERIFY_OFFSET,
         'indicates the start offset in a collection from where to retrieve')
    desc(VERIFY_LIMIT,
         'indicates the number of entities to be retrieved from a collection')
    desc(VERIFY_TOTAL,
         'indicates that the total count of the collection has to be provided')

    if slice_limit_default() is not None:
        desc(VERIFY_LIMIT,
             'if no value is provided it defaults to %(default)s', default=slice_limit_default())
    if slice_limit_maximum() is not None:
        desc(VERIFY_LIMIT,
             'the maximum value is %(maximum)s', maximum=slice_limit_maximum())
    if slice_with_total() is not None:
        desc(VERIFY_TOTAL,
             'if no value is provided it defaults to %(with_total)s', with_total=slice_with_total())
