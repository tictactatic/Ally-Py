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
from ally.api.criteria import AsLikeOrdered
from ally.api.type import Dict, Iter
from ally.support.api.entity_named import Entity, IEntityGetService, QEntity, \
    IEntityQueryService
import hashlib

# --------------------------------------------------------------------

@modelACL(id='Position')
class Entry:
    '''
    The path entry that corresponds to a '*' dynamic path input.
        Position -           the position of the entry in the filter path.
        Type -               the type name associated with the path entry.
    '''
    Position = int
    Type = str

@modelACL
class Filter(Entity):
    '''
    Contains data required for an ACL filter.
        Path -       contains the path that the filter maps to. The path contains beside the fixed string
                     names also markers '*' for where the filtered values or injected values will be placed.
        Hash -       the hash that represents the full aspect of the filter.
        Target -     the target entry position for the filter.
    '''
    Path = str
    Target = Entry
    Hash = str

@modelACL(name=Filter)
class FilterCreate(Filter):
    '''
    Contains data required for creating an ACL filter.
        Types -      the types dictionary needs to have entries as there are '*' in the filter 'Path', the dictionary
                     key is the position of the '*' starting from 1 for the first '*', and as a value the type name.
    '''
    Types = Dict(int, str)
    
# --------------------------------------------------------------------

@query(Filter)
class QFilter(QEntity):
    '''
    Provides the query for filter.
    '''
    path = AsLikeOrdered

# --------------------------------------------------------------------

@service((Entity, Filter), (QEntity, QFilter))
class IFilterService(IEntityGetService, IEntityQueryService):
    '''
    The ACL access filter service provides the means of accessing the available filters.
    '''
    
    @call
    def getEntry(self, filterName:Filter, position:Entry) -> Entry:
        '''
        Provides the path dynamic entry for filter and position.
        '''
        
    @call
    def getEntries(self, filterName:Filter) -> Iter(Entry.Position):
        '''
        Provides the path dynamic entries for filter.
        '''
    
    @call
    def insert(self, filter:FilterCreate) -> Filter.Name:
        '''
        Insert the filter.
        
        @param filter: FilterCreate
            The filter to be inserted.
        @return: string
            The name of the filter.
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

# --------------------------------------------------------------------

def generateHash(filtre):
    '''
    Generates hash for the provided filter create.
    
    @param filtre: FilterCreate
        The filter to generate the has for.
    @return: string
        The generated hash.
    '''
    assert isinstance(filtre, FilterCreate), 'Invalid filter %s' % filtre
    
    hashFil = hashlib.md5()
    hashFil.update(filtre.Name.encode())
    if filtre.Target: hashFil.update(str(filtre.Target).encode())
    if filtre.Types:
        for position in sorted(filtre.Types):
            hashFil.update(('%s:%s' % (position, filtre.Types[position])).encode())
    
    return hashFil.hexdigest().upper()
