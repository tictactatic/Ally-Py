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

# --------------------------------------------------------------------

class IDecoder(metaclass=abc.ABCMeta):
    '''
    The decoder specification.
    '''
    
    @abc.abstractmethod
    def decode(self, path, obj, target, support):
        '''
        Decode the value based on the path in to the provided objects.
        
        @param path: deque(object)
            The path containing elements to identify where the value should be placed.
        @param obj: object
            The value to be placed on the path.
        @param target: object
            The target object to decode in.
        @param support: object
            Support context object containing additional data required for encoding.
        @return: boolean
            True if the decode was successful, False otherwise.
        '''
        
# --------------------------------------------------------------------

class EncoderWithSpecifiers(IEncoder):
    '''
    Support implementation for a @see: IEncoder that also contains @see: ISpecifier.
    '''
    
    def __init__(self, specifiers=None):
        '''
        Construct the encoder with modifiers.
        
        @param specifiers: list[ISpecifier]|tuple(ISpecifier)|None
            The specifiers of the encoder.
        '''
        if __debug__:
            if specifiers:
                assert isinstance(specifiers, (list, tuple)), 'Invalid specifiers %s' % specifiers
                for specifier in specifiers: assert isinstance(specifier, ISpecifier), 'Invalid specifier %s' % specifier
                
        self.specifiers = specifiers
        
    def populate(self, obj, support, **specifications):
        '''
        Populates based on the contained specifiers the provided specifications.
        
        @param obj: object
            The value object to process based on.
        @param support: object
            Support context object containing additional data required for processing.
        @param specifications: key arguments
            The rendering specifications to process.
        @return: dictionary{string: object}
            The rendering specifications.
        '''
        if self.specifiers:
            for specifier in self.specifiers:
                assert isinstance(specifier, ISpecifier), 'Invalid specifier %s' % specifier
                specifier.populate(obj, specifications, support)
        return specifications
