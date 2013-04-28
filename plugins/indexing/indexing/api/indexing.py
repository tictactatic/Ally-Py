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

@modelIndexing(id='Name')
class Action:
    '''
    Provides the action of a block, as defined in @see: ally.indexing.spec.model.Action
    '''
    Name = str
    Before = List(str)
    Final = bool
    Rewind = bool

@modelIndexing
class Perform:
    '''
    Provides the perform of an action, as defined in @see: ally.indexing.spec.model.Perform
    '''
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
    def getBlocks(self) -> Iter(Block):
        '''
        Provides all indexing blocks.
        '''
        
    @call
    def getActions(self, blockId:Block.Id) -> Iter(Action):
        '''
        Provides all indexing actions for block.
        '''
        
    @call
    def getPerforms(self, blockId:Block.Id, actionName:Action.Name) -> Iter(Perform):
        '''
        Provides all performs for action name.
        '''
        
