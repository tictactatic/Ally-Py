'''
Created on Jun 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the primitive types decoding.
'''

from ally.api.type import Type, Iter
from ally.container.ioc import injected
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import requires, defines
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_spec import IDo
from ally.design.processor.context import Context

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    doDecode = defines(IDo, doc='''
    @rtype: callable(value, arguments, support)
    Decodes the value into the provided arguments.
    @param value: object
        The value to be decoded.
    @param arguments: dictionary{string: object}
        The decoded arguments.
    @param support: Context
        Support context object containing additional data required for decoding.
    ''')
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    doSet = requires(IDo)
    
class Support(Context):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Required
    converter = requires(Converter)
    doFailure = requires(IDo)
    
# --------------------------------------------------------------------

@injected
class PrimitiveDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the primitive parameters values decoding.
    '''
    
    def __init__(self):
        super().__init__(Support=Support)
        
    def process(self, chain, decoding:Decoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the primitive decode.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if decoding.doDecode: return
        if isinstance(decoding.type, Iter): return  # Cannot handle a collection, just move along.
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
        def doDecode(value, arguments, support):
            '''
            Do decode the primitive.
            '''
            assert isinstance(support, Support), 'Invalid support %s' % support
            assert isinstance(support.converter, Converter), 'Invalid converter %s' % support.converter
            assert isinstance(decoding, Decoding)
    
            try: value = support.converter.asValue(value, decoding.type)
            except ValueError:
                support.doFailure(decoding, value)
            else: decoding.doSet(arguments, value)
        return doDecode
