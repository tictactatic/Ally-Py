'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for access group.
'''

from .access import Access, Entry, Property
from .domain_acl import modelACL
from .filter import Filter
from ally.api.config import service, call, DELETE, UPDATE
from ally.api.option import SliceAndTotal # @UnusedImport
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
    def getPropertiesFiltered(self, name:Group.Name, accessId:Access) -> Iter(Property.Name):
        '''
        Provides the filtered properties for the group access.
        '''
        
    @call
    def getPropertyFilters(self, name:Group.Name, accessId:Access, propName:Property) -> Iter(Filter.Name):
        '''
        Provides the filters for the group access property.
        '''
    
    @call
    def addGroup(self, accessId:Access.Id, name:Group.Name) -> bool:
        '''
        Adds a new group for the access. The group will also propagate to the shadow, shadowing and shadowed accesses.
        '''
        
    @call(method=DELETE)
    def remGroup(self, accessId:Access, name:Group) -> bool:
        '''
        Removes the group for the access. The group will also propagate to the shadow, shadowing and shadowed accesses.
        '''
        
    @call(method=UPDATE)
    def registerFilter(self, accessId:Access.Id, groupName:Group.Name, filterName:Filter.Name, place:str=None) -> bool:
        '''
        Register a new filter for access, the place is used only when the filter matches multiple entries in the access
        path, the location of the filter will be marked '#'. The register will also propagate to the shadow, shadowing and 
        shadowed accesses.
        '''
    
    @call
    def addEntryFilter(self, accessId:Access.Id, groupName:Group.Name, position:Entry, filterName:Filter.Name) -> bool:
        '''
        Adds the filter to the access group for entry
        '''
        
    @call(method=DELETE)
    def remEntryFilter(self, accessId:Access.Id, groupName:Group.Name, position:Entry, filterName:Filter.Name) -> bool:
        '''
        Removes the filter from the access group for entry
        '''
        
    @call
    def addPropertyFilter(self, accessId:Access.Id, groupName:Group.Name, propName:Property, filterName:Filter.Name) -> bool:
        '''
        Adds the filter to the access group for property
        '''
        
    @call(method=DELETE)
    def remPropertyFilter(self, accessId:Access.Id, groupName:Group.Name, propName:Property, filterName:Filter.Name) -> bool:
        '''
        Removes the filter from the access group for property
        '''
   
