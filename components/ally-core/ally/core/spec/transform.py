'''
Created on Jul 18, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides transformation specifications. 
'''

import abc

# --------------------------------------------------------------------

class ITransfrom(metaclass=abc.ABCMeta):
    '''
    The transform specification.
    '''
    
    @abc.abstractmethod
    def transform(self, value, target, support):
        '''
        Transforms the value into the provided target.
        
        @param value: object
            The value to be transformed.
        @param target: object
            The target to be used to place the transformed value.
        @param support: Context
            Support context object containing additional data required for transforming.
        '''

# --------------------------------------------------------------------

class ISpecifier(metaclass=abc.ABCMeta):
    '''
    The specifications modifier for rendering.
    '''
    
    @abc.abstractmethod
    def populate(self, value, specifications, support):
        '''
        Populates the rendering specifications before being used by an encoder.
        
        @param value: object
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
