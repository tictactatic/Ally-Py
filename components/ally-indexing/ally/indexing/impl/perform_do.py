'''
Created on Apr 25, 2013

@package: ally indexing
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the perform do.
'''

from ..spec.model import Perform, Index
from ..spec.modifier import Content
from ..spec.stream import ModifierStream
from ally.support.util_io import IInputStream
from inspect import isfunction
import re

# --------------------------------------------------------------------

processors = {}
def processor(fn):
    '''
    Decorator for functions to be used as a processor. The processor function will be automatically converted
    into a prepare call that does nothing.
    
    @param fn: function
        The function to be registered as a processor.
    '''
    assert isfunction(fn), 'Invalid function %s' % fn
    processors[fn.__name__] = fn
    return fn

# --------------------------------------------------------------------

@processor
def skip(index, perform, value):
    '''
    Skip action perform, if the content stream is already passed or equal to index nothing will be done.
    '''
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(content.source, ModifierStream), 'Invalid content source %s' % content.source
        content.source.discard(offset(index, perform))
    return do

@processor
def push(index, perform, value):
    '''
    Push the index value action perform, if the content stream is already passed or equal to index nothing will be pushed.
    '''
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(perform.name, str), 'Invalid perform name %s' % perform.name
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(content.source, ModifierStream), 'Invalid content source %s' % content.source
        assert callable(content.decode), 'Invalid content decode %s' % content.decode
        assert isinstance(values, dict), 'Invalid values %s' % values
        
        stack = values.get(perform.name)
        if stack is None: stack = values[perform.name] = []
        nbytes = length(index, perform, content)
        if nbytes > 0: stack.append(content.decode(content.source.read(nbytes)))
        else: stack.append(None)
    return do

@processor
def pushValue(index, perform, value):
    '''
    Push the value action perform.
    '''
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(perform.name, str), 'Invalid perform name %s' % perform.name
        assert isinstance(values, dict), 'Invalid values %s' % values
        
        stack = values.get(perform.name)
        if stack is None: stack = values[perform.name] = []
        if perform.value is None: stack.append(None)
        else: stack.append(perform.value)
    return do

@processor
def pushKey(index, perform, value):
    '''
    Push the value of a block key.
    '''
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(index, Index), 'Invalid index %s' % index
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(perform.key, str), 'Invalid perform key %s' % perform.key
        assert isinstance(perform.name, str), 'Invalid perform name %s' % perform.name
        assert isinstance(values, dict), 'Invalid values %s' % values
        
        stack = values.get(perform.name)
        if stack is None: stack = values[perform.name] = []
        stack.append(index.values.get(perform.key))
    return do

@processor
def pop(index, perform, value):
    '''
    Pops the last value for the provided name.
    '''
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(perform.name, str), 'Invalid perform name %s' % perform.name
        assert isinstance(values, dict), 'Invalid values %s' % values
        
        stack = values.get(perform.name)
        if stack:
            assert isinstance(stack, list), 'Invalid stack %s' % stack
            stack.pop()
    return do
    
@processor
def feed(index, perform, value):
    '''
    Stream action perform, if the content stream is already passed or equal to index nothing will be streamed.
    '''
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(content.source, ModifierStream), 'Invalid content source %s' % content.source
        assert isinstance(content.maximum, int), 'Invalid maximum package size %s' % content.maximum
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        
        nbytes = length(index, perform, content)
        while nbytes > 0:
            if nbytes <= content.maximum: pack = content.source.read(nbytes)
            else: pack = content.source.read(content.maximum)
            if pack == b'': return
            nbytes -= len(pack)
            yield content.encode(pack)
    return do

@processor
def feedValue(index, perform, value):
    '''
    Stream a value action perform.
    '''
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(perform.value, str), 'Invalid perform value %s' % perform.value
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        
        return content.encode(perform.value)
    return do

@processor
def feedKey(index, perform, value):
    '''
    Stream the value for the block key action perform.
    '''
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(index, Index), 'Invalid index %s' % index
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(perform.key, str), 'Invalid perform key %s' % perform.key
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        
        value = index.values.get(perform.key)
        if value is not None: return content.encode(value)
    return do
    
@processor
def feedName(index, perform, value):
    '''
    Stream the value for name action perform.
    '''
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        assert isinstance(values, dict), 'Invalid values %s' % values
        
        stack = values.get(perform.name)
        if stack:
            assert isinstance(stack, list), 'Invalid stack %s' % stack
            return content.encode(stack[-1])
    return do

@processor
def feedContent(index, perform, value):
    '''
    Stream proxy side content action perform.
    '''
    if value is None: return
    if not isinstance(value, (str, Content)): return
    if isinstance(value, Content):
        assert isinstance(value, Content)
        if not isinstance(value.source, IInputStream): return
        if not callable(value.decode) or not callable(value.encode): return
        
    def do(content, values, flags):
        if not hasFlags(perform, flags): return
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(content.maximum, int), 'Invalid maximum package size %s' % content.maximum
        assert callable(content.encode), 'Invalid content encode %s' % content.encode
        assert callable(content.decode), 'Invalid content decode %s' % content.decode
        
        if isinstance(value, str):
            if perform.escapes: encode = escaped(content.decode, content.encode, perform.escapes)
            else: encode = content.encode
            yield encode(value)
        else:
            assert isinstance(value, Content)
            assert isinstance(value.source, IInputStream)
            if perform.escapes: encode = escaped(value.decode, value.encode, perform.escapes)
            else: encode = value.encode

            while True:
                pack = value.source.read(content.maximum)
                if pack == b'': break
                yield encode(pack)
    return do

# --------------------------------------------------------------------

@processor
def setFlag(index, perform, value):
    '''
    Set flag action perform.
    '''
    def do(content, values, flags):
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(flags, set), 'Invalid flags %s' % flags
    
        if perform.flags: flags.update(perform.flags)
    return do

@processor
def setFlagIfBefore(index, perform, value):
    '''
    Set flag action perform in case the current stream index is before the provided index.
    '''
    def do(content, values, flags):
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(flags, set), 'Invalid flags %s' % flags
    
        if perform.flags and length(index, perform, content) > 0: flags.update(perform.flags)
    return do

@processor
def setFlagIfNotBefore(index, perform, value):
    '''
    Set flag action perform in case the current stream index is not before the provided index, this
    means either after or equal to current index.
    '''
    def do(content, values, flags):
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(flags, set), 'Invalid flags %s' % flags
    
        if perform.flags and length(index, perform, content) <= 0: flags.update(perform.flags)
    return do
    
@processor
def remFlag(index, perform, value):
    '''
    Remove flag action perform.
    '''
    def do(content, values, flags):
        assert isinstance(perform, Perform), 'Invalid perform %s' % perform
        assert isinstance(flags, set), 'Invalid flags %s' % flags
    
        if perform.flags: flags.difference_update(perform.flags)
    return do

# --------------------------------------------------------------------

def hasFlags(perform, flags):
    '''
    Checks if the do perform checks the flags from the execution repository.
    
    @return: boolean
        True if the flags check, False otherwise.
    '''
    assert isinstance(perform, Perform), 'Invalid perform %s' % perform
    assert isinstance(flags, set), 'Invalid flags %s' % flags

    if not perform.flags: return True
    return flags.issuperset(perform.flags)

def offset(index, perform):
    '''
    Provides the offset of the perform index.
    
    @return: integer
        The perform index offset.
    '''
    assert isinstance(index, Index), 'Invalid index %s' % index
    assert isinstance(perform, Perform), 'Invalid perform %s' % perform
    
    return index.values[perform.index]

def length(index, perform, content):
    '''
    Provides the length of the current stream offset and the perform index offset.
    
    @return: integer
        The length from current stream offset to perform index offset.
    '''
    assert isinstance(content, Content), 'Invalid content %s' % content
    assert isinstance(content.source, ModifierStream), 'Invalid content source %s' % content.source
    
    return offset(index, perform) - content.source.tell()

def escaped(decode, encode, escapes):
    '''
    Provides the encode that escapes for content.

    @param decode: callable(bytes) -> string
        The decoder that converts from the response encoding bytes to string.
    @param encode: callable(bytes|string) -> bytes
        The encoder that converts from the source encoding or an arbitrary string to the expected encoding.
    @param escapes: dictionary{string: stirng}
        The escapes dictionary.
    @return: callable(string|bytes) -> bytes
        The encoder with escaping.
    '''
    assert callable(decode), 'Invalid decode %s' % decode
    assert callable(encode), 'Invalid encode %s' % encode
    assert isinstance(escapes, dict), 'Invalid escapes %s' % escapes
    assert escapes, 'No escapes provided'
    
    regex = re.compile('|'.join('(%s)' % re.escape(escaped) for escaped in escapes))
    replacer = lambda match: escapes[match.group(0)]
    def escape(content):
        if not isinstance(content, str): content = decode(content)
        content = regex.sub(replacer, content)
        return encode(content)
    return escape
