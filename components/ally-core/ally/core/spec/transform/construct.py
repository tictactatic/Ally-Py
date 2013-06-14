'''
Created on Jun 14, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides transforming object to construct content. 
'''

import abc

# --------------------------------------------------------------------

class IDevise(metaclass=abc.ABCMeta):
    '''
    The specification for the constructor of decoded objects.
    '''
    __slots__ = ()
    
    @abc.abstractclassmethod
    def get(self, target):
        '''
        Get the value represented by the constructor from the provided target.
        
        @param target: object
            The target to get the value from.
        @return: object
            The constructed object from the target.
        '''
        
    @abc.abstractclassmethod
    def set(self, target, value):
        '''
        Set the constructed value into the provided target.
        
        @param target: object
            The target to set the value to.
        @param value: object
            The value object to set to the target.
        '''

# --------------------------------------------------------------------

class DeviseDict(IDevise):
    '''
    Implementation for @see: IDevise that handles the value for a target dictionary based on a predefined key.
    '''
    __slots__ = ('key',)
    
    def __init__(self, key):
        '''
        Construct the dictionary devise.
        
        @param key: object
            The key to be used on the target dictionary.
        '''
        self.key = key
        
    def get(self, target):
        '''
        @see: IDevise.get
        
        Provides None if the key is not presssent.
        '''
        assert isinstance(target, dict), 'Invalid target %s' % target
        return target.get(self.key)
    
    def set(self, target, value):
        '''
        @see: IDevise.set
        '''
        assert isinstance(target, dict), 'Invalid target %s' % target
        target[self.key] = value
