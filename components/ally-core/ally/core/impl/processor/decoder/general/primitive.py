'''
Created on Jun 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the primitive types decoding.
'''

from ally.api.type import Type, Iter, Dict
from ally.container.ioc import injected
from ally.core.impl.processor.base import FailureTarget, addFailure
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_spec import IDo

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    doDecode = defines(IDo, doc='''
    @rtype: callable(target, value)
    Decodes the value into the provided target.
    @param target: Context
        Target context object used for decoding.
    @param value: object
        The value to be decoded.
    ''')
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    doSet = requires(IDo)
    
class Target(FailureTarget):
    '''
    The target context.
    '''
    # ---------------------------------------------------------------- Required
    converter = requires(Converter)
    
# --------------------------------------------------------------------

@injected
class PrimitiveDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the primitive parameters values decoding.
    '''
    
    def __init__(self):
        super().__init__(Target=Target)
        
    def process(self, chain, decoding:Decoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the primitive decode.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if decoding.doDecode: return
        if isinstance(decoding.type, (Iter, Dict)): return  # Cannot handle a collection, just move along.
        if not decoding.type.isPrimitive: return  # If the type is not primitive just move along.
        
        decoding.doDecode = self.createDecode(decoding)
        
    # ----------------------------------------------------------------
    
    def createDecode(self, decoding):
        '''
        Create the primitive do decode.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(decoding.doSet, IDo), 'Invalid decoding do set %s' % decoding.doSet
        assert isinstance(decoding.type, Type), 'Invalid decoding type %s' % decoding.type
        def doDecode(target, value):
            '''
            Do decode the primitive.
            '''
            assert isinstance(target, Target), 'Invalid target %s' % target
            assert isinstance(target.converter, Converter), 'Invalid converter %s' % target.converter
            assert isinstance(decoding, Decoding)
    
            try: value = target.converter.asValue(value, decoding.type)
            except ValueError: addFailure(target, decoding, value=value)
            else: decoding.doSet(target, value)
        return doDecode
