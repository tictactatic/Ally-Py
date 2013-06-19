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

# --------------------------------------------------------------------

class IDecoder(metaclass=abc.ABCMeta):
    '''
    The decoder specification.
    '''
    
    @abc.abstractmethod
    def decode(self, path, obj, target, support):
        '''
        Decode the value based on the path in to the provided objects.
        
        @param path: object
            The path describing where the value should be placed.
        @param obj: object
            The value to be placed on the path.
        @param target: object
            The target object to decode in.
        @param support: object
            Support context object containing additional data required for decoding.
        @return: boolean|None
            If True it means that the decoding has been performed on the provided data.
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
    def set(self, target, value, support):
        '''
        Set the constructed value into the provided target.
        
        @param target: object
            The target to set the value to.
        @param value: object
            The value object to set to the target.
        @param support: object
            Support context object containing additional data.
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

class DecoderDelegate(IDecoder):
    '''
    Implementation for a @see: IDecoder that delegates to other decoders unitl one is succesful in decoding.
    '''
    
    def __init__(self, decoders):
        '''
        Construct the delegate decoder.
        '''
        assert isinstance(decoders, list), 'Invalid decoders %s' % decoders
        assert decoders, 'At leas on decoder is required'
        if __debug__:
            for decoder in decoders: assert isinstance(decoder, IDecoder), 'Invalid decoder %s' % decoder
        
        self.decoders = decoders
        
    def decode(self, path, obj, target, support):
        '''
        @see: IDecoder.decode
        '''
        assert isinstance(path, str), 'Invalid path %s' % path
        
        for decoder in self.decoders:
            assert isinstance(decoder, IDecoder), 'Invalid decoder %s' % decoder
            if decoder.decode(path, obj, target, support): return True
    
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
    
    def set(self, target, value, support):
        '''
        @see: IDevise.set
        '''
        assert isinstance(target, dict), 'Invalid target %s' % target
        target[self.key] = value
