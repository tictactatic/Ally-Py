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
    def populate(self, obj, attributes, support, index=None):
        '''
        Populates the attributes to be used by an encoder.
        
        @param obj: object
            The value object to provide attributes based on.
        @param attributes: dictionary{string: string}
            The attributes dictionary to populate.
        @param support: object
            Support object containing additional data required for attributes.
        @param index: list[Index]|None
            The list of index requests to push for rendering, None if no indexes are allowed from attributes.
        '''

# --------------------------------------------------------------------

class EncoderWithAttributes(IEncoder):
    '''
    Support implementation for a @see: IEncoder that also contains @see: IAttributes.
    '''
    
    def __init__(self, attributes=None):
        '''
        Construct the encoder with attributes.
        
        @param attributes: IAttributes|None
            The attributes of the encoder.
        '''
        assert attributes is None or isinstance(attributes, IAttributes), 'Invalid attributes %s' % attributes
        
        self.attributes = attributes
        
    # ----------------------------------------------------------------
    
    def processAttributes(self, obj, support, index=None):
        '''
        Fetches the attributes.
        
        @param obj: object
            The value object to provide attributes based on.
        @param index: list[Index]
            The list of index requests to push for rendering.
        @return: dictionary{string: string}|None
            The attributes dictionary, or None if there are no attributes.
        @param support: object
            Support object containing additional data required for attributes.
        '''
        if self.attributes is None: return
        attributes = {}
        self.attributes.populate(obj, attributes, support, index)
        return attributes
    
class AttributesWrapper(IAttributes):
    '''
    Implementation for @see: IAttributes that wraps optionally other attributes.
    '''
    
    def __init__(self, attributes=None):
        '''
        Construct the wrapped attributes.
        
        @param attributes: IAttributes|None
            The attributes to join with.
        '''
        assert attributes is None or isinstance(attributes, IAttributes), 'Invalid attributes %s' % attributes
        
        self.attributes = attributes
    
    def populate(self, obj, attributes, support, index=None):
        '''
        @see: IAttributes.populate
        '''
        if self.attributes: self.attributes.populate(obj, attributes, support, index)
        
