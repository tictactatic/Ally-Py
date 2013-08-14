'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for service filters.
'''

from .access import Access
from .domain_acl import modelACL
from .group import Group
from .method import Method
from ally.api.config import service, call
from ally.api.type import Iter
from ally.support.api.entity_named import Entity, IEntityGetService, \
    IEntityFindService

# --------------------------------------------------------------------

@modelACL
class Allowed:
    '''
    Defines the allowed model that is returned by filters.
    '''
    IsAllowed = bool
    
@modelACL
class Filter(Entity):
    '''
    The filter model.
    '''

# --------------------------------------------------------------------

@service((Entity, Filter))
class IFilterService(IEntityGetService, IEntityFindService):
    '''
    The ACL access filter service provides the means of accessing the available filters.
    '''
    
    @call
    def getFilters(self, access:Access, method:Method, group:Group) -> Iter(Filter.Name):
        '''
        Provides the group filters.
        '''
    
    @call
    def addFilter(self, access:Access.Name, method:Method.Name, group:Group.Name, filter:Filter.Name, hint:str=None) -> bool:
        '''
        Adds the filter for the access group, the hint is used only when the filter matches multiple entries in the access
        path, the location of the filter will be marked '#'.
        '''
        
    @call
    def removeFilter(self, access:Access, method:Method, group:Group, filter:Filter) -> bool:
        '''
        Removes the filter for the access group.
        '''
