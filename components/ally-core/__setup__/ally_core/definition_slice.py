'''
Created on Jul 14, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the slice definitions.
'''

from .definition import definitionDescribers, addDescriber
from .resources import slice_limit_default, slice_limit_maximum, \
    slice_with_total
from ally.api.option import Slice, SliceAndTotal
from ally.container import ioc
from ally.core.impl.verifier import VerifyType
from ally.support.api.util_service import isCompatible

# --------------------------------------------------------------------

@ioc.after(definitionDescribers)
def updateDescribersForSlice():
    # This is based on @see:  optionSlice().
    if slice_limit_default() is not None:
        addDescriber(VerifyType(Slice.limit, check=isCompatible),
                     'if no value is provided it defaults to %s' % slice_limit_default())
    if slice_limit_maximum() is not None:
        addDescriber(VerifyType(Slice.limit, check=isCompatible),
                     'the maximum value is %s' % slice_limit_maximum())
    if slice_with_total() is not None:
        addDescriber(VerifyType(SliceAndTotal.withTotal, check=isCompatible),
                     'if no value is provided it defaults to %s' % slice_with_total())
