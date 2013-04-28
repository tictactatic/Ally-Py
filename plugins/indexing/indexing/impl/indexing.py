'''
Created on Apr 26, 2013

@package: indexing
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for indexing data.
'''

from ..api.indexing import IIndexingService, Block, Action, Perform
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.indexing.spec import model

# --------------------------------------------------------------------

class Mapping(Context):
    '''
    The index mapping context.
    '''
    # ---------------------------------------------------------------- Required
    blockId = requires(int)
    block = requires(model.Block)
    
class Blocks(Context):
    '''
    The blocks index context.
    '''
    # ---------------------------------------------------------------- Required
    blocks = requires(dict)

# --------------------------------------------------------------------

@injected
@setup(IIndexingService, name='indexingService')
class AssemblageMarkerService(IIndexingService):
    '''
    Implementation for @see: IAssemblageMarkerService.
    '''
    
    assemblyBlocks = Assembly; wire.entity('assemblyBlocks')
    # The block processors to be used for fetching the indexes.
    
    def __init__(self):
        assert isinstance(self.assemblyBlocks, Assembly), 'Invalid blocks assembly %s' % self.assemblyBlocks
        
        self._processingBlocks = self.assemblyBlocks.create(blocks=Blocks, Mapping=Mapping)
        self._blocks = None
        self._actions = None
        self._performs = None
        
    def getBlocks(self):
        '''
        @see: IIndexingService.getBlocks
        '''
        self._process()
        return self._blocks
    
    def getActions(self, blockId):
        '''
        @see: IIndexingService.getActions
        '''
        assert isinstance(blockId, int), 'Invalid block id %s' % blockId
        self._process()
        return self._actions.get(blockId, ())
        
    def getPerforms(self, blockId, actionName):
        '''
        @see: IIndexingService.getPerforms
        '''
        assert isinstance(blockId, int), 'Invalid block id %s' % blockId
        assert isinstance(actionName, str), 'Invalid action name %s' % actionName
        self._process()
        return self._performs.get((blockId, actionName), ())
        
    # ----------------------------------------------------------------
    
    def _process(self):
        '''
        Process the entities.
        '''
        if self._blocks is not None: return
        
        self._blocks = []
        self._actions = {}
        self._performs = {}
        
        proc = self._processingBlocks
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        chain = Chain(proc)
        chain.process(**proc.fillIn()).doAll()
        assert isinstance(chain.arg.blocks, Blocks), 'Invalid blocks %s' % chain.arg.blocks
        assert isinstance(chain.arg.blocks.blocks, dict), 'Invalid blocks %s' % chain.arg.blocks.blocks
        
        for name, mapping in chain.arg.blocks.blocks.items():
            assert isinstance(mapping, Mapping), 'Invalid mapping %s' % mapping
            assert isinstance(mapping.block, model.Block), 'Invalid block %s' % mapping.block
            
            block = Block()
            block.Id = mapping.blockId
            block.Name = name
            if mapping.block.keys: block.Keys = mapping.block.keys
            self._blocks.append(block)
            
            actions = []
            for maction in mapping.block.actions:
                assert isinstance(maction, model.Action), 'Invalid action %s' % maction
                
                performs = []
                for mperform in maction.performs:
                    assert isinstance(mperform, model.Perform), 'Invalid perform %s' % mperform
                    perform = Perform()
                    perform.Verb = mperform.verb
                    if mperform.flags: perform.Flags = mperform.flags
                    perform.Index = mperform.index
                    perform.Key = mperform.key
                    perform.Name = mperform.name
                    perform.Value = mperform.value
                    if mperform.actions: perform.Actions = mperform.actions
                    if mperform.escapes: perform.Escapes = mperform.escapes
                    performs.append(perform)
                self._performs[(mapping.blockId, maction.name)] = performs
                
                action = Action()
                action.Name = maction.name
                action.Final = maction.final
                action.Rewind = maction.rewind
                if maction.before: action.Before = maction.before
                actions.append(action)
            actions.sort(key=lambda action: action.Name)
            self._actions[mapping.blockId] = actions
            
        self._blocks.sort(key=lambda block: block.Id)
