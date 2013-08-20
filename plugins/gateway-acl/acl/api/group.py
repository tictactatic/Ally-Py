'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for access group.
'''

from .access import Access, Entry
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
        Provides also the groups allowed for access.
        '''

    @call    
    def getAccesses(self, name:Group.Name, **options:SliceAndTotal) -> Iter(Access.Id):
        '''
        Provides the allowed access for the group.
        '''
    
    @call
    def getEntriesFiltered(self, name:Group.Name, accessId:Access) -> Iter(Entry.Position):
        '''
        Provides the filtered entries for the group access.
        '''
        
    @call
    def getEntryFilters(self, name:Group.Name, accessId:Access, position:Entry) -> Iter(Filter.Name):
        '''
        Provides the filters for the group access entry.
        '''
        
    @call
    def addGroup(self, accessId:Access.Id, name:Group.Name) -> bool:
        '''
        Adds a new group for the access.
        '''
        
    @call(method=DELETE)
    def remGroup(self, accessId:Access, name:Group) -> bool:
        '''
        Removes the group for the access.
        '''
        
    @call
    def addFilter(self, accessId:Access.Id, groupName:Group.Name, filterName:Filter.Name, place:str=None) -> bool:
        '''
        Adds a new filter for access, the place is used only when the filter matches multiple entries in the access
        path, the location of the filter will be marked '#'.
        '''
        
    @call(method=DELETE)
    def remFilter(self, accessId:Access.Id, groupName:Group.Name, position:Entry, filterName:Filter.Name) -> bool:
        '''
        Removes the filter from the access group for entry
        '''
   
