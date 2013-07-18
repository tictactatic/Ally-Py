'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides encoder decoder specifications. 
'''

import abc

# --------------------------------------------------------------------

# TODO: Gabriel: unify encoder and decoder into one ITransfrom api

class IEncoder(metaclass=abc.ABCMeta):
    '''
    The encoder specification.
    '''
    
    @abc.abstractmethod
    def encode(self, obj, target, support):
        '''
        Renders the value in to the provided renderer.
        
        @param obj: object
            The value object to be encoded.
        @param target: object
            The target to be used to place the encoded value.
        @param support: object
            Support context object containing additional data required for encoding.
        '''

class IDecoder(metaclass=abc.ABCMeta):
    '''
    The decoder specification.
    '''
    
    @abc.abstractmethod
    def decode(self, value, target, support):
        '''
        Decode the value based into the provided target.
        
        @param value: object
            The value to be placed on the path.
        @param target: object
            The target object to decode in.
        @param support: object
            Support context object containing additional data required for decoding.
        '''

# --------------------------------------------------------------------

class ISpecifier(metaclass=abc.ABCMeta):
    '''
    The specifications modifier for rendering.
    '''
    
    @abc.abstractmethod
    def populate(self, obj, specifications, support):
        '''
        Populates the rendering specifications before being used by an encoder.
        
        @param obj: object
            The value object to process based on.
        @param specifications: dictionary{string: object}
            The rendering specifications to process.
        @param support: object
            Support context object containing additional data required for processing.
        '''

class IRender(metaclass=abc.ABCMeta):
    '''
    The specification for the renderer of encoded objects.
    '''
    __slots__ = ()

    @abc.abstractclassmethod
    def property(self, name, value, **specifications):
        '''
        Called to signal that a property value has to be rendered.

        @param name: string
            The property name.
        @param value: string|tuple(string)|list[string]|dictionary{string: string}
            The value.
        @param specifications: key arguments
            Additional key arguments specifications dictating the rendering.
        '''

    @abc.abstractclassmethod
    def beginObject(self, name, **specifications):
        '''
        Called to signal that an object has to be rendered.
        
        @param name: string
            The object name.
        @param specifications: key arguments
            Additional key arguments specifications dictating the rendering.
        @return: self
            The same render instance for chaining purposes.
        '''

    @abc.abstractclassmethod
    def beginCollection(self, name, **specifications):
        '''
        Called to signal that a collection of objects has to be rendered.
        
        @param name: string
            The collection name.
        @param specifications: key arguments
            Additional key arguments specifications dictating the rendering.
        @return: self
            The same render instance for chaining purposes.
        '''

    @abc.abstractclassmethod
    def end(self):
        '''
        Called to signal that the current block (object or collection) has ended the rendering.
        '''

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
