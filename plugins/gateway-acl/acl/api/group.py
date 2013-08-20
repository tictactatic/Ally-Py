'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for access group.
'''

from .access import Access
from .domain_acl import modelACL
from .filter import Filter
from ally.api.config import service, call, DELETE
from ally.api.option import SliceAndTotal  # @UnusedImport
from ally.api.type import Iter
from ally.support.api.entity_named import Entity, IEntityNQService

# --------------------------------------------------------------------

@modelACL
class Group(Entity):
    '''
    Defines the group of ACL access,
    '''
    Description = str

# --------------------------------------------------------------------

@service((Entity, Group))
class IGroupService(IEntityNQService):
    '''
    The ACL access group service used for allowing accesses based on group.
    '''
    
    @call
    def getAll(self, accessId:Access=None, **options:SliceAndTotal) -> Iter(Group.Name):
        '''
        @see: IEntityNQService.getAll
        Provides the groups allowed also for access.
        '''
        
    @call
    def getFilters(self, accessId:Access, name:Group.Name, **options:SliceAndTotal) -> Iter(Filter.Name):
        '''
        Provides the filters for the access group.
        '''
        
    @call
    def addGroup(self, accessId:Access.Id, name:Group.Name) -> bool:
        '''
        Adds a new group for the access.
        '''
        
    @call
    def addFilter(self, accessId:Access.Id, groupName:Group.Name, filterName:Filter.Name, place:str=None) -> bool:
        '''
        Adds a new allowed access, the place is used only when the filter matches multiple entries in the access
        path, the location of the filter will be marked '#'.
        '''
        
    @call(method=DELETE)
    def remGroup(self, accessId:Access, name:Group) -> bool:
        '''
        Removes the group for the access.
        '''
   
