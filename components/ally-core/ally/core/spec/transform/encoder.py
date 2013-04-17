'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides encoder specifications. 
'''

import abc

# --------------------------------------------------------------------

class IEncoder(metaclass=abc.ABCMeta):
    '''
    The encoder specification.
    '''
    
    @abc.abstractmethod
    def render(self, obj, render, support):
        '''
        Renders the value in to the provided renderer.
        
        @param obj: object
            The value object to be rendered.
        @param render: IRender
            The renderer to be used to output the encoded value.
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
