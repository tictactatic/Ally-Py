'''
Created on Jul 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides aid contexts and support functions that are generally used.
'''

from ally.core.spec.codes import Coded
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from collections import Iterable

# --------------------------------------------------------------------

class ErrorResponse(Coded):
    '''
    The error response context.
    '''
    # ---------------------------------------------------------------- Defined
    errors = defines(list, doc='''
    @rtype: list[tuple(list[string], dictionary{string: object}, list[Context]]
    Contains the error messages and definition contexts that have not been respected, on the first position the error
    messages on the second the data used for messages place holders and on the last the definition context that the
    error is targeting.
    ''')

# --------------------------------------------------------------------

def addError(response, *items, **data):
    '''
    Adds a new error messages.
    
    @param response: Context
        The response context to add the error to.
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
    assert isinstance(response, ErrorResponse), 'Invalid context %s' % response
    
    if response.errors is None: response.errors = []
    response.errors.append((messages, data, contexts))

# --------------------------------------------------------------------

class FailureTarget(Context):
    '''
    The target failure context.
    '''
    # ---------------------------------------------------------------- Required
    failures = defines(list, doc='''
    @rtype: list[tuple(Context, object, list[string], dictionary{string: object})]
    Contains the decode failures as a list containing tuples having on the first position the decoding context that
    reported the failure, on the second position the value that have failed decoding, on the third position the messages
    associated with the failure and on the last position the data used for messages place holders.
    ''')
      
# --------------------------------------------------------------------

def addFailure(target, decoding, *messages, value=None, **data):
    '''
    Adds a new failure entry.
    
    @param target: Context
        The target context to add the failure to.
    @param decoding: Context
        The decoding context to add the failure to.
    @param messages: arguments[string|Iterable(string)]
        The failure messages to add.
    @param value: object
        The value that is the failure target.
    @param data: key arguments
        Data to be used for messages place holders.
    '''
    assert isinstance(target, FailureTarget), 'Invalid target context %s' % target
    assert isinstance(decoding, Context), 'Invalid context %s' % decoding
    msgs = []
    for message in messages:
        if isinstance(message, str): msgs.append(message)
        else:
            assert isinstance(message, Iterable), 'Invalid message %s' % message
            for msg in message:
                assert isinstance(msg, str), 'Invalid message %s' % msg
                msgs.append(msg)
    
    if target.failures is None: target.failures = []
    target.failures.append((decoding, value, msgs, data))
