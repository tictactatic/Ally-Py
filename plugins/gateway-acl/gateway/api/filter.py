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
    def getFilters(self, access:Access, group:Group=None, method:Method=None) -> Iter(Filter.Name):
        '''
        Provides the available filters.
        '''
    
    @call
    def addFilter(self, access:Access.Name, group:Group.Name, method:Method.Name, filter:Filter.Name) -> bool:
        '''
        Adds the filter for the access group.
        '''
        
    @call
    def removeFilter(self, access:Access, group:Group, method:Method, filter:Filter) -> bool:
        '''
        Removes the filter for the access group.
        '''
