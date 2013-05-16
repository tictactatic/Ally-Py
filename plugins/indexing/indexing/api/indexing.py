'''
Created on Apr 23, 2013

@package: indexing
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the API for indexing service provider.
'''

from .domain_indexing import modelIndexing
from ally.api.config import service, call
from ally.api.type import Iter, Dict, List

# --------------------------------------------------------------------

@modelIndexing(id='Id')
class Block:
    '''
    Provides the index block, as defined in @see: ally.indexing.spec.model.Block
    '''
    Id = int
    Name = str
    Keys = List(str)

@modelIndexing(id='Id')
class Action:
    '''
    Provides the action of a block, as defined in @see: ally.indexing.spec.model.Action
    '''
    Id = int
    Name = str
    Before = List(str)
    Final = bool
    Rewind = bool

@modelIndexing(id='Id')
class Perform:
    '''
    Provides the perform of an action, as defined in @see: ally.indexing.spec.model.Perform
    '''
    Id = int
    Verb = str
    Flags = List(str)
    Index = str
    Key = str
    Name = str
    Value = str
    Actions = List(str)
    Escapes = Dict(str, str)

# --------------------------------------------------------------------

@service
class IIndexingService:
    '''
    Provides the indexing service.
    '''
    
    @call
    def getBlock(self, blockId:Block.Id) -> Block:
        '''
        Provides the block for id.
        '''
    
    @call
    def getAction(self, actionId:Action.Id) -> Action:
        '''
        Provides the action for id.
        '''
    
    @call
    def getPerform(self, performId:Perform.Id) -> Perform:
        '''
        Provides the perform for id.
        '''
        
    @call
    def getBlocks(self) -> Iter(Block.Id):
        '''
        Provides all indexing blocks.
        '''
        
    @call
    def getActions(self, blockId:Block.Id) -> Iter(Action.Id):
        '''
        Provides all indexing actions for block.
        '''
        
    @call
    def getPerforms(self, actionId:Action.Id) -> Iter(Perform.Id):
        '''
        Provides all performs for action id.
        '''
        
