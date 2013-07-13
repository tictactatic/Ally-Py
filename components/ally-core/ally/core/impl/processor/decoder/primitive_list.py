'''
Created on Jul 12, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the primitive list types decoding.
'''

from .primitive import PrimitiveDecode, Support
from ally.api.type import Type, Iter
from ally.container.ioc import injected
from ally.core.spec.resources import Converter
from ally.core.spec.transform.encdec import IDecoder, IDevise
from collections import Iterable

# --------------------------------------------------------------------

@injected
class PrimitiveListDecode(PrimitiveDecode):
    '''
    Extension for @see: PrimitiveDecode for a handler that provides the primitive list values decoding.
    '''
            
    def createDecoder(self, objType, path, devise):
        '''
        @see: PrimitiveDecode.createDecoder
        '''
        if not isinstance(objType, Iter): return
        # Not a list, just move along.
        assert isinstance(objType, Iter)
        if not objType.isPrimitive: return
        # If the type is not primitive just move along.
        return DecoderSimpleList(path, devise, objType.itemType)

# --------------------------------------------------------------------

class DecoderSimpleList(IDecoder):
    '''
    Implementation for a @see: IDecoder for simple list types.
    '''
    
    def __init__(self, path, devise, itemType):
        '''
        Construct the simple list type decoder.
        '''
        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
        assert isinstance(itemType, Type), 'Invalid item type %s' % itemType
        
        self.path = path
        self.devise = devise
        self.itemType = itemType
        
    def decode(self, path, obj, target, support):
        '''
        @see: IDecoder.decode
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.converter, Converter), 'Invalid converter %s' % support.converter
        
        if not isinstance(obj, Iterable): obj = (obj,)

        values = []
        for item in obj:
            if isinstance(item, str):
                try: values.append(support.converter.asValue(item, self.itemType))
                except ValueError: pass
                else: continue
                
            if support.failures is None: support.failures = []
            support.failures.append('Invalid item \'%s\' for \'%s\'' % (item, path))
            
        previous = self.devise.get(target)
        if previous is None: self.devise.set(target, values, support)
        else:
            assert isinstance(previous, list), 'Invalid previous value %s' % previous
            previous.extend(values)
        return True
