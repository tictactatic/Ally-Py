'''
Created on Apr 25, 2013

@package: ally indexing
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides support for creating standard performs.
'''

from .model import Perform
from ally.support.util_sys import callerName

# --------------------------------------------------------------------
        
def skip(index, *flags):
    '''
    Skip action perform, if the content stream is already passed or equal to index nothing will be done.
    
    @param index: string
        The index name to skip at.
    @param flags: arguments[string]
        The flags that need to be set in order for the skip to be performed.
    '''
    assert isinstance(index, str), 'Invalid index %s' % index
    return Perform(callerName(0), *flags, index=index)
        
def push(name, index, *flags):
    '''
    Push the index value action perform, if the content stream is already passed or equal to index nothing will be pushed.
    
    @param name: string
        The name to push the value with.
    @param index: string
        The index name to use for getting the value to push.
    @param flags: arguments[string]
        The flags that need to be set in order for the push to be performed.
    '''
    assert isinstance(name, str), 'Invalid name %s' % name
    assert isinstance(index, str), 'Invalid index %s' % index
    return Perform(callerName(0), *flags, index=index, name=name)

def pushValue(name, value, *flags):
    '''
    Push the value action perform.
    
    @param name: string
        The name to push the block name with.
    @param value: string
        The value to be pushed.
    @param flags: arguments[string]
        The flags that need to be set in order for the push to be performed.
    '''
    assert isinstance(name, str), 'Invalid name %s' % name
    assert isinstance(value, str), 'Invalid value %s' % value
    return Perform(callerName(0), *flags, name=name, value=value)

def pushKey(name, key, *flags):
    '''
    Push the value of a block key.
    
    @param name: string
        The name to push the value with.
    @param key: string
        The block key to get the value to push.
    @param flags: arguments[string]
        The flags that need to be set in order for the push to be performed.
    '''
    assert isinstance(name, str), 'Invalid name %s' % name
    assert isinstance(key, str), 'Invalid key %s' % key
    return Perform(callerName(0), *flags, key=key, name=name)

def pop(name, *flags):
    '''
    Pops the last value for the provided name.
    
    @param name: string
        The name to pop the value for.
    @param flags: arguments[string]
        The flags that need to be set in order for the pop to be performed.
    '''
    assert isinstance(name, str), 'Invalid name %s' % name
    return Perform(callerName(0), *flags, name=name)

def feed(index, *flags):
    '''
    Stream action perform, if the content stream is already passed or equal to index nothing will be streamed.
    
    @param index: string
        The index name to stream at.
    @param flags: arguments[string]
        The flags that need to be set in order for the stream to be performed.
    '''
    assert isinstance(index, str), 'Invalid index %s' % index
    return Perform(callerName(0), *flags, index=index)

def feedValue(value, *flags):
    '''
    Stream a value action perform.

    @param value: string
        The value to be streamed.
    @param flags: arguments[string]
        The flags that need to be set in order for the stream to be performed.
    '''
    assert isinstance(value, str), 'Invalid value %s' % value
    return Perform(callerName(0), *flags, value=value)

def feedKey(key, *flags):
    '''
    Stream the value for the block key action perform.

    @param key: string
        The block key to stream the value for.
    @param flags: arguments[string]
        The flags that need to be set in order for the stream to be performed.
    '''
    assert isinstance(key, str), 'Invalid key %s' % key
    return Perform(callerName(0), *flags, key=key)

def feedName(name, *flags):
    '''
    Stream the value for name action perform.

    @param name: string
        The name to have the value streamed.
    @param flags: arguments[string]
        The flags that need to be set in order for the stream to be performed.
    '''
    assert isinstance(name, str), 'Invalid value %s' % name
    return Perform(callerName(0), *flags, name=name)
        
def feedContent(*flags, escapes=None):
    '''
    Stream proxy side content action perform.
    
    @param flags: arguments[string]
        The flags that need to be set in order for the stream to be performed.
    @param escapes: dictionary{string: string}
        The escape dictionary, as a key the value that needs to be escaped and as a value the replacing value.
    '''
    return Perform(callerName(0), *flags, escapes=escapes)

def feedIndexed(*flags, actions=None):
    '''
    Stream proxy side indexed content action perform.
    
    @param flags: arguments[string]
        The flags that need to be set in order for the stream to be performed.
    @param actions: Iterable(string)|None
        The action names to be passed to the indexed content to be streamed.
    '''
    return Perform(callerName(0), *flags, actions=actions)

# --------------------------------------------------------------------

def setFlag(*flags):
    '''
    Set flag action perform.
    
    @param flags: arguments[string]
        The flags to be set.
    '''
    assert flags, 'At least one flag is required'
    return Perform(callerName(0), *flags)

def setFlagIfBefore(index, *flags):
    '''
    Set flag action perform in case the current stream index is before the provided index.
    
    @param index: string
        The index name that needs to be after (not even equal).
    @param flags: arguments[string]
        The flags to be set.
    '''
    assert isinstance(index, str), 'Invalid index %s' % index
    assert flags, 'At least one flag is required'
    return Perform(callerName(0), *flags, index=index)

def setFlagIfNotBefore(index, *flags):
    '''
    Set flag action perform in case the current stream index is not before the provided index, this
    means either after or equal to current index.
    
    @param index: string
        The index name that needs to be before (or equal).
    @param flags: arguments[string]
        The flags to be set.
    '''
    assert isinstance(index, str), 'Invalid index %s' % index
    assert flags, 'At least one flag is required'
    return Perform(callerName(0), *flags, index=index)

def remFlag(*flags):
    '''
    Remove flag action perform.
    
    @param flags: arguments[string]
        The flags to be removed.
    '''
    assert flags, 'At least one flag is required'
    return Perform(callerName(0), *flags)
