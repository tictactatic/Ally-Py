'''
Created on Jul 15, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the list string exploding.
'''

from ally.api.type import Type, List, String
from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_spec import IDo
import re

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    parameterDefinition = requires(Context)
    doDecode = requires(IDo)

class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Required
    types = requires(list)
                    
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
        super().__init__(Definition=Definition)
        
    def process(self, chain, decoding:Decoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Wrap with explode decoders.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if not decoding.doDecode: return
        
        if not isinstance(decoding.type, List): return  # The type is not a list, just move along.
        assert isinstance(decoding.type, List)
        
        decoding.doDecode = self.createExplode(decoding.doDecode)
        
        if decoding.parameterDefinition:
            assert isinstance(decoding.parameterDefinition, Definition), \
            'Invalid definition %s' % decoding.parameterDefinition
            assert isinstance(decoding.parameterDefinition.types, list), \
            'Invalid definition %s' % decoding.parameterDefinition.types
            decoding.parameterDefinition.types.append(String)

    # ----------------------------------------------------------------
    
    def createExplode(self, decode):
        '''
        Create the do explode decode.
        '''
        assert isinstance(decode, IDo), 'Invalid decode %s' % decode
        def doDecode(value, arguments, support):
            '''
            Do the explode decode.
            '''
            if isinstance(value, str):
                value = self.regexSplit.split(value)
                for k in range(0, len(value)): value[k] = self.regexNormalize.sub('', value[k])
                
            decode(value, arguments, support)
        return doDecode
