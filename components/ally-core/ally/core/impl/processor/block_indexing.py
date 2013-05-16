'''
Created on Apr 17, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the handler for providing the index blocks mappings.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.indexing.spec.model import Block
from ally.support.util import firstOf

# --------------------------------------------------------------------

class MappingIndex(Context):
    '''
    The index mapping context.
    '''
    # ---------------------------------------------------------------- Defined
    blockId = defines(int, doc='''
    @rtype: integer
    The block id.
    ''')
    block = defines(Block, doc='''
    @rtype: Block
    The block represented by the mapping.
    ''')

class Blocks(Context):
    '''
    The blocks index context.
    '''
    # ---------------------------------------------------------------- Defined
    blocks = defines(dict, doc='''
    @rtype: dictionary{string: MappingIndex}
    A dictionary containing the mappings indexed by the block name.
    ''')
    
# --------------------------------------------------------------------

@injected
class BlockIndexingHandler(HandlerProcessor):
    '''
    Provides the block indexing.
    '''
    
    definitions = dict
    # The dictionary containing the block definitions.
    
    def __init__(self):
        assert isinstance(self.definitions, dict), 'Invalid block definitions %s' % self.definitions
        if __debug__:
            for name, block in self.definitions.items():
                assert isinstance(name, str), 'Invalid block name %s' % name
                assert isinstance(block, Block), 'Invalid block %s' % block
        super().__init__()
        
    def process(self, chain, blocks:Blocks, Mapping:MappingIndex, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the indexed blocks.
        '''
        assert isinstance(blocks, Blocks), 'Invalid index blocks %s' % blocks
        assert issubclass(Mapping, MappingIndex), 'Invalid index mapping class %s' % Mapping
        
        if blocks.blocks is None: blocks.blocks = {}
        
        for id, (name, block) in enumerate(sorted(self.definitions.items(), key=firstOf), 1):  # We order by name
            blocks.blocks[name] = Mapping(blockId=id, block=block)
