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
    __slots__ = ('source', 'indexes', 'maximum', 'doEncode', 'doDecode')
    
    def __init__(self, source, indexes=None, maximum=1024, doEncode=None, doDecode=None):
        '''
        Construct the data content with indexes.
        
        @param source: IInputStream
            The source of the content.
        @param indexes: list[Index]|None
            The indexes for the stream.
        @param maximum: integer
            The maximum bytes package size.
        @param doEncode: callable(bytes|string) -> bytes|None
            The encoder that converts from the source encoding or an arbitrary string to the expected encoding.
        @param doDecode: callable(bytes) -> string|None
            The decoder that converts from the response encoding bytes to string.
        '''
        assert isinstance(source, IInputStream), 'Invalid source stream %s' % source
        assert isinstance(maximum, int), 'Invalid maximum %s' % maximum
        assert doEncode is None or callable(doEncode), 'Invalid do encode %s' % doEncode
        assert doDecode is None or callable(doDecode), 'Invalid do decode %s' % doDecode
        if __debug__:
            if indexes:
                assert isinstance(indexes, list), 'Invalid indexes %s' % indexes
                for index in indexes: assert isinstance(index, Index), 'Invalid index %s' % index
        self.source = ModifierStream(source)
        self.indexes = indexes
        self.maximum = maximum
        self.doEncode = doEncode
        self.doDecode = doDecode

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
