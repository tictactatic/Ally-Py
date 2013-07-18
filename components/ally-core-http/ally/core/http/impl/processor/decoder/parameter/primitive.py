'''
Created on Jun 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the primitive types parameter decoding.
'''

from ally.api.type import Type, Iter
from ally.container.ioc import injected
from ally.core.impl.processor.decoder.base import DefineDecoding, SupportFailure
from ally.core.spec.resources import Converter
from ally.core.spec.transform.encdec import IDecoder, IDevise
from ally.design.processor.attribute import requires
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Support(SupportFailure):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Required
    converterPath = requires(Converter)
    
# --------------------------------------------------------------------

@injected
class PrimitiveDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the primitive parameters values decoding.
    '''
    
    def __init__(self):
        super().__init__(Support=Support)
        
    def process(self, chain, decoding:DefineDecoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the primitive decode.
        '''
        assert isinstance(decoding, DefineDecoding), 'Invalid decoding %s' % decoding
        
        if decoding.decoder: return
        if isinstance(decoding.type, Iter): return  # Cannot handle a collection, just move along.
        if not decoding.type.isPrimitive: return  # If the type is not primitive just move along.
        
        decoding.decoder = DecoderPrimitive(decoding.devise, decoding.type, decoding)
            
# --------------------------------------------------------------------

class DecoderPrimitive(IDecoder):
    '''
    Implementation for a @see: IDecoder for primitve types.
    '''
    
    def __init__(self, devise, type, decoding):
        '''
        Construct the simple type decoder.
        '''
        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
        assert isinstance(type, Type), 'Invalid type %s' % type
        
        self.devise = devise
        self.type = type
        self.decoding = decoding
        
    def decode(self, value, target, support):
        '''
        @see: IDecoder.decode
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.converterPath, Converter), 'Invalid converter %s' % support.converterPath
        
        try: value = support.converterPath.asValue(value, self.type)
        except ValueError:
            if support.failures is None: support.failures = []
            support.failures.append((value, self.decoding))
        else: self.devise.set(target, value, support)
    
