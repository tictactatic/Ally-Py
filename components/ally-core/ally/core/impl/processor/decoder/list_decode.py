'''
Created on Jul 15, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the list decoding.
'''

from ally.api.type import List
from ally.container.ioc import injected
from ally.core.impl.processor.decoder.base import DefineDecoding
from ally.core.spec.transform.encdec import IDevise, IDecoder
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import definesIf, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranching
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Decoding(DefineDecoding):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    parent = defines(Context, doc='''
    @rtype: Context
    The parent decoding that this decoding is based on.
    ''')
    isCorrupted = definesIf(bool, doc='''
    @rtype: boolean
    Flag indicating that the decoding is corrupted.
    ''')
    
# --------------------------------------------------------------------

@injected
class ListDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the list decoding.
    '''
    
    listAssembly = Assembly
    # The list item decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.listAssembly, Assembly), 'Invalid list assembly %s' % self.listAssembly
        super().__init__(Branch(self.listAssembly).included())

    def process(self, chain, processing, decoding:Decoding, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Populate the list decoder.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if decoding.decoder: return
        if not isinstance(decoding.type, List): return  # The type is not a list, just move along.
        assert isinstance(decoding.type, List)
        
        idecoding = decoding.__class__()
        assert isinstance(idecoding, Decoding), 'Invalid decoding %s' % idecoding
        
        idecoding.parent = decoding
        idecoding.devise = DeviseList(decoding.devise)
        idecoding.type = decoding.type.itemType
        
        arg = processing.executeWithAll(decoding=idecoding, **keyargs)
        assert isinstance(arg.decoding, Decoding), 'Invalid decoding %s' % arg.decoding
        
        if arg.decoding.decoder: decoding.decoder = DecoderList(arg.decoding.decoder)
        elif Decoding.isCorrupted in arg.decoding and Decoding.isCorrupted in decoding:
            if arg.decoding.isCorrupted:
                log.error('Cannot decode list item %s', decoding.type.itemType)
                decoding.isCorrupted = True
                chain.cancel()

# --------------------------------------------------------------------

class DeviseList(IDevise):
    '''
    Implementation for @see: IDevise for handling lists.
    '''
    
    def __init__(self, devise):
        '''
        Construct the devise for lists.
        '''
        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
        
        self.devise = devise
        
    def get(self, target):
        '''
        @see: IDevise.get
        '''
        return None
        
    def set(self, target, value):
        '''
        @see: IDevise.set
        '''
        previous = self.devise.get(target)
        if previous is None: self.devise.set(target, [value])
        else:
            assert isinstance(previous, list), 'Invalid previous value %s' % previous
            previous.append(value)

class DecoderList(IDecoder):
    '''
    Implementation for a @see: IDecoder for list types.
    '''
    
    def __init__(self, decoder):
        '''
        Construct the simple list type decoder.
        '''
        assert isinstance(decoder, IDecoder), 'Invalid decoder %s' % decoder
        self.decoder = decoder
        
    def decode(self, value, target, support):
        '''
        @see: IDecoder.decode
        '''
        assert isinstance(value, list), 'Invalid value %s' % value
        for item in value: self.decoder(item, target, support)
