'''
Created on Sep 3, 2013

@package: gui action
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Gociu

Provides the actions category support.
'''

from .action import Action
from ally.api.config import prototype
from ally.api.option import SliceAndTotal  # @UnusedImport
from ally.api.type import Iter
import abc  # @UnusedImport

# --------------------------------------------------------------------

class IActionCategoryPrototype(metaclass=abc.ABCMeta):
    '''
    The ACL access prototype service used for allowing accesses based on other entities.
    '''
    
    @prototype
    def getActions(self, idnetifier:lambda p:p.CATEGORY, **options:SliceAndTotal) -> Iter(Action.Path):
        '''
        Provides the ACL objects for the provided access id.
        
        @param accessId: integer
            The access id to provide the ACL for.
        @param options: key arguments
            The result iteration options.
        @return: Iterable(ACL.identifier)
            An iterator containing the ACL objects identifiers.
        '''
