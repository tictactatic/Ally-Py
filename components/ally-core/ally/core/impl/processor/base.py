'''
Created on Jul 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides aid contexts and support functions that are generally used.
'''

from ally.design.processor.context import Context
from ally.design.processor.attribute import defines
from collections import Iterable
from ally.core.spec.codes import Coded

# --------------------------------------------------------------------

class ErrorResponse(Coded):
    '''
    The error response context.
    '''
    # ---------------------------------------------------------------- Defined
    errors = defines(list, doc='''
    @rtype: list[tuple(list[string], dictionary{string: object}, list[Context]]
    Contains the error messages or definition contexts that have not been respected.
    ''')

# --------------------------------------------------------------------

def addError(context, *items, **data):
    '''
    Adds a new error messages.
    
    @param context: Context
        The context to add the error to.
    @param items: arguments[string|Iterable(string)|Context|Iterable(Context)]
        The error messages to add.
    @param data: key arguments
        Data to be used for messages place holders.
    '''
    assert items, 'At least one item is required'
    messages, contexts = [], []
    for item in items:
        if isinstance(item, str): messages.append(item)
        elif isinstance(item, Context): contexts.append(item)
        else:
            assert isinstance(item, Iterable), 'Invalid item %s' % item
            for it in item:
                if isinstance(it, str): messages.append(it)
                else:
                    assert isinstance(it, Context), 'Invalid item %s' % it
                    contexts.append(it)
    assert isinstance(context, ErrorResponse), 'Invalid context %s' % context
    
    if context.errors is None: context.errors = []
    context.errors.append((messages, data, contexts))
