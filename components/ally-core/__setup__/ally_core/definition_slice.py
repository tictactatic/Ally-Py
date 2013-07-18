'''
Created on Jul 14, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the slice definitions.
'''

from .definition import desc, descriptions
from .resources import slice_limit_default, slice_limit_maximum, \
    slice_with_total
from ally.api.option import Slice, SliceAndTotal
from ally.container import ioc
from ally.core.impl.definition import InputType
from ally.support.api.util_service import isCompatible

# --------------------------------------------------------------------

@ioc.before(descriptions)
def updateDescriptionsForSlice():
    # This is based on @see:  optionSlice().
    if slice_limit_default() is not None:
        desc(InputType(Slice.limit, check=isCompatible),
             'if no value is provided it defaults to %(default)s', default=slice_limit_default())
    if slice_limit_maximum() is not None:
        desc(InputType(Slice.limit, check=isCompatible),
             'the maximum value is %(maximum)s', maximum=slice_limit_maximum())
    if slice_with_total() is not None:
        desc(InputType(SliceAndTotal.withTotal, check=isCompatible),
             'if no value is provided it defaults to %(with_total)s', with_total=slice_with_total())
