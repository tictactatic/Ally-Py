'''
Created on Jul 15, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the list string exploding.
'''

from ally.api.type import Type, List
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IDecoder
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
import re

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    decoder = requires(IDecoder)
    
# --------------------------------------------------------------------

@injected
class ExplodeDecode(HandlerProcessor):
    '''
    Implementation for a list explode to values from a string value.
    '''
    
    regexSplit = re.compile('[\s]*(?<!\\\)\,[\s]*')
    # The regex used for splitting list values.
    regexNormalize = re.compile('\\\(?=\,)')
    # The regex used for normalizing the split values.
    
    def __init__(self):
        assert self.regexSplit, 'Invalid regex for values split %s' % self.regexSplit
        assert self.regexNormalize, 'Invalid regex for value normalize %s' % self.regexNormalize
        super().__init__()
        
    def process(self, chain, decoding:Decoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Wrap with explode decoders.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if not decoding.decoder: return
        if not isinstance(decoding.type, List): return  # The type is not a list, just move along.
        assert isinstance(decoding.type, List)
        
        decoding.decoder = DecoderExploded(self.regexSplit, self.regexNormalize, decoding.decoder)
        
        assert isinstance(decoding.decoder, IDecoder), 'Invalid decoder %s' % decoding.decoder

# --------------------------------------------------------------------

class DecoderExploded(IDecoder):
    '''
    Implementation for a @see: IDecoder for exploded values.
    '''
    
    def __init__(self, split, normalize, decoder):
        '''
        Construct the exploded list type decoder.
        '''
        assert split, 'Invalid regex for values split %s' % split
        assert normalize, 'Invalid regex for value normalize %s' % normalize
        assert isinstance(decoder, IDecoder), 'Invalid decoder %s' % decoder
        
        self.split = split
        self.normalize = normalize
        self.decoder = decoder
        
    def decode(self, value, target, support):
        '''
        @see: IDecoder.decode
        '''
        if isinstance(value, str):
            value = self.split.split(value)
            for k in range(0, len(value)): value[k] = self.normalize.sub('', value[k])
            
        self.decoder.decode(value, target, support)
