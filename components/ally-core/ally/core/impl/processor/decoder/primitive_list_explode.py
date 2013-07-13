'''
Created on Jul 12, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the primitive exploded list types decoding.
'''

from .primitive import PrimitiveDecode, Support
from .primitive_list import DecoderSimpleList
from ally.api.type import Iter
from ally.container.ioc import injected
from ally.core.spec.resources import Converter
import re
 
# --------------------------------------------------------------------

@injected
class PrimitiveListExplodeDecode(PrimitiveDecode):
    '''
    Extension for @see: PrimitiveDecode for a handler that provides the primitive exploded list values decoding.
    '''
    
    regexSplit = re.compile('[\s]*(?<!\\\)\,[\s]*')
    # The regex used for splitting list values.
    regexNormalize = re.compile('\\\(?=\,)')
    # The regex used for normalizing the split values.
    
    def __init__(self):
        assert self.regexSplit, 'Invalid regex for values split %s' % self.regexSplit
        assert self.regexNormalize, 'Invalid regex for value normalize %s' % self.regexNormalize
        super().__init__()
        
    def createDecoder(self, objType, path, devise):
        '''
        @see: PrimitiveDecode.createDecoder
        '''
        if not isinstance(objType, Iter): return
        # Not a list, just move along.
        assert isinstance(objType, Iter)
        if not objType.isPrimitive: return
        # If the type is not primitive just move along.
        return DecoderExplodedList(path, devise, objType.itemType, self.regexSplit, self.regexNormalize)

# --------------------------------------------------------------------

class DecoderExplodedList(DecoderSimpleList):
    '''
    Extension for a @see: DecoderSimpleList for simple list types with exploded values.
    '''
    
    def __init__(self, path, devise, itemType, split, normalize):
        '''
        Construct the simple list type decoder.
        '''
        assert split, 'Invalid regex for values split %s' % split
        assert normalize, 'Invalid regex for value normalize %s' % normalize
        super().__init__(path, devise, itemType)
        
        self.split = split
        self.normalize = normalize
        
    def decode(self, path, obj, target, support):
        '''
        @see: IDecoder.decode
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.converter, Converter), 'Invalid converter %s' % support.converter
        
        if path != self.path: return
        if isinstance(obj, str):
            obj = self.split.split(obj)
            for k in range(0, len(obj)): obj[k] = self.normalize.sub('', obj[k])
        
        return super().decode(path, obj, target, support)
