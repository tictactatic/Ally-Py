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
            Support object containing additional data required for encoding.
        '''

class IAttributes(metaclass=abc.ABCMeta):
    '''
    The attributes provider specification.
    '''
    
    @abc.abstractmethod
    def provide(self, obj, support):
        '''
        Returns the attributes to be used by an encoder.
        
        @param obj: object
            The value object to provide attributes based on.
        @param support: object
            Support object containing additional data required for attributes.
        @return: dictionary{string: string}|None
            The attributes to be used by the encoder.
        '''

# --------------------------------------------------------------------

class AttributesJoiner(IAttributes):
    '''
    Implementation for @see: IAttributes that wraps other attributes and then joins the two returned attributes.
    '''
    
    def __init__(self, attributes=None):
        '''
        Construct the wrapped attributes.
        
        @param attributes: IAttributes|None
            The attributes to join with.
        '''
        assert attributes is None or isinstance(attributes, IAttributes), 'Invalid attributes %s' % attributes
        
        self.attributes = attributes
    
    def provide(self, obj, support):
        '''
        @see: IAttributes.provide
        '''
        attributes = self.provideIntern(obj, support)
        
        if self.attributes: other = self.attributes.provide(obj, support)
        else: other = None
        
        if not other: return attributes
        elif attributes:
            assert isinstance(other, dict), 'Invalid other attributes %s' % other
            other.update(attributes)
        return other
        
    # ----------------------------------------------------------------
    
    @abc.abstractmethod
    def provideIntern(self, obj, support):
        '''
        Same as @see: IAttributes.provide but is for internal purpose, doesn't need to care about the joined attributes.
        '''
