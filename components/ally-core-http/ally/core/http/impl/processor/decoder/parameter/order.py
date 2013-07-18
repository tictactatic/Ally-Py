'''
Created on Jun 19, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the queries ascending and descending order criteria decoding.
'''

from ally.api.criteria import AsOrdered
from ally.api.operator.type import TypeProperty
from ally.api.type import List, typeFor
from ally.container.ioc import injected
from ally.core.impl.processor.decoder.base import DefineCreate, SupportFailure, \
    DefineDecoding
from ally.core.spec.transform.encdec import IDevise, IDecoder
from ally.design.processor.attribute import requires, defines
from ally.design.processor.handler import HandlerProcessor
from ally.support.api.util_service import isCompatible

# --------------------------------------------------------------------

class DecodingOrder(DefineDecoding):
    '''
    The order decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    enumeration = defines(list, doc='''
    @rtype: list[string]
    The enumeration values that are allowed for order.
    ''')
    # ---------------------------------------------------------------- Required
    path = requires(list)
    property = requires(TypeProperty)
    
# --------------------------------------------------------------------

@injected
class OrderDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the query order criterias decoding.
    '''
    
    nameAsc = 'asc'
    # The name used for the ascending list of names.
    nameDesc = 'desc'
    # The name used for the descending list of names.
    separator = '.'
    # The separator to use for parameter names.
    
    def __init__(self):
        assert isinstance(self.nameAsc, str), 'Invalid name for ascending %s' % self.nameAsc
        assert isinstance(self.nameDesc, str), 'Invalid name for descending %s' % self.nameDesc
        assert isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__(Support=SupportFailure)
        
    def process(self, chain, create:DefineCreate, Decoding:DecodingOrder, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the order decode.
        '''
        assert isinstance(create, DefineCreate), 'Invalid create %s' % create
        assert issubclass(Decoding, DecodingOrder), 'Invalid decoding class %s' % Decoding
        
        if not create.decodings: return 
        # There is not decodings to process.
        
        k, ascending, priority = 0, {}, {}
        while k < len(create.decodings):
            decoding = create.decodings[k]
            k += 1
            
            assert isinstance(decoding, DecodingOrder), 'Invalid decoding %s' % decoding
            if not decoding.path or not decoding.property: continue
            
            if isCompatible(AsOrdered.ascending, decoding.property):
                assert isinstance(decoding.devise, IDevise), 'Invalid devise %s' % decoding.devise
                ascending[self.separator.join(decoding.path[:-1])] = decoding.devise
            elif isCompatible(AsOrdered.priority, decoding.property):
                assert isinstance(decoding.devise, IDevise), 'Invalid devise %s' % decoding.devise
                priority[self.separator.join(decoding.path[:-1])] = decoding.devise
            else: continue
            # Is not an ordered criteria.
            
            k -= 1
            del create.decodings[k]
            
        if ascending:
            adec, ddec = Decoding(), Decoding()
            assert isinstance(adec, DecodingOrder), 'Invalid decoding %s' % adec
            assert isinstance(ddec, DecodingOrder), 'Invalid decoding %s' % ddec
            create.decodings.append(adec)
            create.decodings.append(ddec)
            
            adec.decoder = DecoderOrder(True, ascending, priority, adec)
            adec.path = [self.nameAsc]
            adec.enumeration = sorted(ascending.keys())
            
            ddec.decoder = DecoderOrder(False, ascending, priority, ddec)
            ddec.path = [self.nameDesc]
            ddec.enumeration = list(adec.enumeration)
            
            adec.type = ddec.type = typeFor(List(str))

# --------------------------------------------------------------------

class DecoderOrder(IDecoder):
    '''
    Implementation for a @see: IDecoder for queries order.
    '''
    
    def __init__(self, asc, ascending, priority, decoding):
        '''
        Construct the order decoder.
        '''
        assert isinstance(asc, bool), 'Invalid ascending flag %s' % asc
        assert isinstance(ascending, dict), 'Invalid ascending mapping %s' % ascending
        assert isinstance(priority, dict), 'Invalid priority mapping %s' % priority
        
        self.asc = asc
        self.ascending = ascending
        self.priority = priority
        self.decoding = decoding
    
    def decode(self, value, target, support):
        '''
        @see: IDecoder.decode
        '''
        assert isinstance(value, list), 'Invalid value %s' % value
        assert isinstance(support, SupportFailure), 'Invalid support %s' % support
        for item in value:
            ascending = self.ascending.get(item)
            if ascending is None:
                if support.failures is None: support.failures = []
                support.failures.append((item, self.decoding))
            else:
                assert isinstance(ascending, IDevise), 'Invalid devise %s' % ascending
                ascending.set(target, self.asc)
                priority = self.priority.get(item)
                if priority:
                    assert isinstance(priority, IDevise), 'Invalid devise %s' % priority
                    current = 0
                    for devise in self.priority.values():
                        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
                        val = devise.get(target)
                        if val is not None: current = max(current, val)
                    
                    priority.set(target, current + 1)
