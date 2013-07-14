'''
Created on Jul 14, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides basic implementations for encoder decoder specifications. 
'''

from ally.core.spec.transform.encdec import IEncoder, ISpecifier, IDecoder
   
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
        for decoder in self.decoders:
            assert isinstance(decoder, IDecoder), 'Invalid decoder %s' % decoder
            if decoder.decode(path, obj, target, support): return True
    
