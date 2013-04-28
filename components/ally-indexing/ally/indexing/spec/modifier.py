'''
Created on Apr 25, 2013

@package: ally indexing
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the modifications support specifications.
'''

from .model import Index
from .stream import ModifierStream
from ally.support.util_io import IInputStream
import abc

# --------------------------------------------------------------------

class Content:
    '''
    The content data, this can be extended for additional informations.
    '''
    __slots__ = ('source', 'encode', 'decode', 'indexes', 'maximum')
    
    def __init__(self, source, encode=None, decode=None, indexes=None, maximum=1024):
        '''
        Construct the data content with indexes.
        
        @param source: IInputStream
            The source of the content.
        @param encode: callable(bytes|string) -> bytes|None
            The encoder that converts from the source encoding or an arbitrary string to the expected encoding.
        @param decode: callable(bytes) -> string|None
            The decoder that converts from the response encoding bytes to string.
        @param indexes: list[Index]|None
            The indexes for the stream.
        @param maximum: integer
            The maximum bytes package size.
        '''
        assert isinstance(source, IInputStream), 'Invalid source stream %s' % source
        assert encode is None or callable(encode), 'Invalid encode %s' % encode
        assert decode is None or callable(decode), 'Invalid decode %s' % decode
        assert isinstance(maximum, int), 'Invalid maximum %s' % maximum
        if __debug__:
            if indexes:
                assert isinstance(indexes, list), 'Invalid indexes %s' % indexes
                for index in indexes: assert isinstance(index, Index), 'Invalid index %s' % index
        self.source = ModifierStream(source)
        self.encode = encode
        self.decode = decode
        self.indexes = indexes
        self.maximum = maximum

# --------------------------------------------------------------------

class IModifier(metaclass=abc.ABCMeta):
    '''
    Specification for a block modifier.
    '''
    
    @abc.abstractmethod
    def fetch(self, name):
        '''
        Fetches the value for the action.
        
        @param name: string
            The action name to fetch the provided value for.
        @return: string|None
            The value that has been provided by the action, if any.
        '''
    
    @abc.abstractmethod
    def register(self, *names, value=None):
        '''
        Register for modifications the provided action.
        
        @param names: arguments[string]
            The action names to register for modification in the order that they should be registered.
        @param value: object|None
            The value to associate from proxy side with the action.
        @return: boolean
            True if at least one action has been registered, False otherwise.
        '''
        
class IAlter(metaclass=abc.ABCMeta):
    '''
    Specification for altering the block modifier.
    '''
    
    @abc.abstractmethod
    def alter(self, content, modifier):
        '''
        Provide altering action for the modifier.
        
        @param content: Content
            The content being altered.
        @param modifier: IModifier
            The modifier used for altering the content.
        '''
