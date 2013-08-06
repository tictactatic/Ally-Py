'''
Created on Apr 26, 2013

@package: indexing
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for indexing data.
'''

from ..api.indexing import IIndexingService, Block, Action, Perform
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.indexing.spec import model
from collections import OrderedDict

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
        self._blocksById = None
        self._actions = OrderedDict()
        self._actionsById = {}
        self._actionsByBlock = {}
        self._performs = OrderedDict()
        self._performsById = {}
        self._performsByAction = {}
    
    def getBlock(self, blockId):
        '''
        @see: IIndexingService.getAction
        '''
        assert isinstance(blockId, int), 'Invalid block id %s' % blockId
        self._process()
        block = self._blocksById.get(blockId)
        if block is None: raise InvalidIdError()
        return block
    
    def getAction(self, actionId):
        '''
        @see: IIndexingService.getAction
        '''
        assert isinstance(actionId, int), 'Invalid action id %s' % actionId
        self._process()
        action = self._actionsById.get(actionId)
        if action is None: raise InvalidIdError()
        return action
    
    def getPerform(self, performId):
        '''
        @see: IIndexingService.getPerform
        '''
        assert isinstance(performId, int), 'Invalid perform id %s' % performId
        self._process()
        perform = self._performsById.get(performId)
        if perform is None: raise InvalidIdError()
        return perform
        
    def getBlocks(self):
        '''
        @see: IIndexingService.getBlocks
        '''
        self._process()
        return self._blocksById.keys()
    
    def getActions(self, blockId):
        '''
        @see: IIndexingService.getActions
        '''
        assert isinstance(blockId, int), 'Invalid block id %s' % blockId
        self._process()
        return self._actionsByBlock.get(blockId, ())
        
    def getPerforms(self, actionId):
        '''
        @see: IIndexingService.getPerforms
        '''
        assert isinstance(actionId, int), 'Invalid action id %s' % actionId
        self._process()
        return self._performsByAction.get(actionId, ())
        
    # ----------------------------------------------------------------
    
    def _process(self):
        '''
        Process the entities.
        '''
        if self._blocksById is not None: return
        
        blocksList = []
        proc = self._processingBlocks
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        blocks = proc.executeWithAll().blocks
        assert isinstance(blocks, Blocks), 'Invalid blocks %s' % blocks
        assert isinstance(blocks.blocks, dict), 'Invalid blocks %s' % blocks.blocks
        
        for name, mapping in blocks.blocks.items():
            assert isinstance(mapping, Mapping), 'Invalid mapping %s' % mapping
            assert isinstance(mapping.block, model.Block), 'Invalid block %s' % mapping.block
            
            block = Block()
            block.Id = mapping.blockId
            block.Name = name
            if mapping.block.keys: block.Keys = mapping.block.keys
            blocksList.append(block)
            
            actions = []
            for maction in sorted(mapping.block.actions, key=lambda maction: maction.name):
                assert isinstance(maction, model.Action), 'Invalid action %s' % maction
                
                mhash = self._hash(maction)
                action = self._actions.get(mhash)
                if action is not None:
                    actions.append(action.Id)
                    continue
                
                action = Action()
                action.Id = len(self._actions) + 1
                action.Name = maction.name
                action.Final = maction.final
                action.Rewind = maction.rewind
                if maction.before: action.Before = maction.before
                self._actions[mhash] = action
                self._actionsById[action.Id] = action
                actions.append(action.Id)
                
                performs = []
                for mperform in maction.performs:
                    assert isinstance(mperform, model.Perform), 'Invalid perform %s' % mperform
                    
                    phash = self._hash(mperform)
                    perform = self._performs.get(phash)
                    if perform is None:
                        perform = Perform()
                        perform.Id = len(self._performs) + 1
                        perform.Verb = mperform.verb
                        if mperform.flags: perform.Flags = mperform.flags
                        perform.Index = mperform.index
                        perform.Key = mperform.key
                        perform.Name = mperform.name
                        perform.Value = mperform.value
                        if mperform.actions: perform.Actions = mperform.actions
                        if mperform.escapes: perform.Escapes = mperform.escapes
                        self._performs[phash] = perform
                        self._performsById[perform.Id] = perform
                        
                    performs.append(perform.Id)
                    
                self._performsByAction[action.Id] = performs
                
            self._actionsByBlock[mapping.blockId] = actions
        
        blocksList.sort(key=lambda block: block.Id)
        self._blocksById = OrderedDict((block.Id, block) for block in blocksList)
        
    # ----------------------------------------------------------------
    
    def _hash(self, obj):
        '''
        Creates the hash for the index model.
        '''
        if isinstance(obj, model.Action):
            assert isinstance(obj, model.Action)
            return hash((obj.name, obj.performs, obj.before, obj.final, obj.rewind))
        if isinstance(obj, model.Perform):
            assert isinstance(obj, model.Perform)
            return hash((obj.verb, obj.flags, obj.index, obj.key, obj.name, obj.value, obj.actions, obj.escapes))
