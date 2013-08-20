'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for service filters.
'''

from .domain_acl import modelACL
from ally.api.config import service, call, query
from ally.api.criteria import AsEqualOrdered
from ally.api.type import List
from ally.support.api.entity_named import Entity, IEntityGetService, QEntity, \
    IEntityQueryService

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
        Target -     the target type name that this filter is designed for.
        Paths -      a list of paths that are used to check the filter, at least one path needs to provide an allowed
                     answer in order to consider the filter passed. The path contains beside the fixed string
                     names also a marker '*' for where the filtered value should be placed before using the service.
                     The paths might also contain other value place holders.
    '''
    Target = str
    Paths = List(str)

# --------------------------------------------------------------------

@query(Filter)
class QFilter(QEntity):
    '''
    Provides the query for filter.
    '''
    target = AsEqualOrdered

# --------------------------------------------------------------------

@service((Entity, Filter), (QEntity, QFilter))
class IFilterService(IEntityGetService, IEntityQueryService):
    '''
    The ACL access filter service provides the means of accessing the available filters.
    '''
    
    @call
    def insert(self, filter:Filter) -> Filter.Name:
        '''
        Insert the filter.
        
        @param filter: Filter
            The filter to be inserted.
        '''
    
    @call
    def delete(self, name:Filter) -> bool:
        '''
        Delete the filter for the provided name.
        
        @param name: string
            The name of the filter to be deleted.
        @return: boolean
            True if the delete is successful, false otherwise.
        '''
