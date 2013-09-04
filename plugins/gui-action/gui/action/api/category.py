'''
Created on Sep 3, 2013

@package: gui action
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Gociu

Provides the actions category support.
'''

from .action import Action
from ally.api.config import prototype, DELETE
from ally.api.option import SliceAndTotal  # @UnusedImport
from ally.api.type import Iter
from ally.support.api.util_service import modelId
import abc  # @UnusedImport

# --------------------------------------------------------------------

class IActionCategoryGetPrototype(metaclass=abc.ABCMeta):
    '''
    The action category prototype service provides support for fetching actions based on category entities.
    '''
    
    @prototype(webName='All')
    def getActions(self, identifier:lambda p:p.CATEGORY, **options:SliceAndTotal) -> Iter(Action.Path):
        '''
        Provides all the actions paths for the provided identifier.
        
        @param identifier: object
            The action category object identifier.
        @param options: key arguments
            The result iteration options.
        @return: Iterable(Action.Path)
            An iterator containing the action paths.
        '''
    
    @prototype
    def getActionsRoot(self, identifier:lambda p:p.CATEGORY, **options:SliceAndTotal) -> Iter(Action.Path):
        '''
        Provides the root actions paths for the provided identifier.
        
        @param identifier: object
            The action category object identifier.
        @param options: key arguments
            The result iteration options.
        @return: Iterable(Action.Path)
            An iterator containing the root action paths.
        '''
        
    @prototype(webName='Sub')
    def getSubActions(self, identifier:lambda p:p.CATEGORY, parentPath:Action.Path, **options:SliceAndTotal) -> Iter(Action.Path):
        '''
        Provides the actions paths for the provided identifier and parent path.
        
        @param identifier: object
            The action category object identifier.
        @param parentPath: string
            THe parent path to provide the actions for.
        @param options: key arguments
            The result iteration options.
        @return: Iterable(Action.Path)
            An iterator containing the action paths.
        '''

class IActionCategoryPrototype(IActionCategoryGetPrototype):
    '''
    The action category prototype service provides support for registering actions based on category entities.
    '''
        
    @prototype
    def addAction(self, identifier:lambda p: modelId(p.CATEGORY), actionPath:Action.Path):
        '''
        Adds a new action for the action category object identifier.
        
        @param identifier: object
            The action category object identifier.
        @param actionPath: string
            The action path to be added.
        '''
        
    @prototype(method=DELETE)
    def remAction(self, identifier:lambda p: p.CATEGORY, actionPath:Action.Path) -> bool:
        '''
        Removes the action for the action category object identifier.
        
        @param identifier: object
            The action category object identifier.
        @param actionPath: string
            The action path to be removed.
        @return: boolean
            True if an action has been successfully removed, False otherwise. 
        '''
