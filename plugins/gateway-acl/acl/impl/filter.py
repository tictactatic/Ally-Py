'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL filter.
'''

from ..api.filter import FilterCreate, IFilterService, QFilter, generateHash
from ..meta.acl_intern import Path
from ..meta.filter import FilterMapped, FilterEntryMapped
from acl.core.impl.acl_intern import pathId, typeId
from ally.api.error import InputError
from ally.container.ioc import injected
from ally.container.support import setup
from ally.internationalization import _
from ally.support.sqlalchemy.util_service import deleteModel, iterateCollection
from sql_alchemy.impl.entity import EntityGetServiceAlchemy, \
    EntityQueryServiceAlchemy, EntitySupportAlchemy
    
# --------------------------------------------------------------------

@injected
@setup(IFilterService, name='filterService')
class FilterServiceAlchemy(EntityGetServiceAlchemy, EntityQueryServiceAlchemy, IFilterService):
    '''
    Implementation for @see: IFilterService that provides the ACL filters.
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, FilterMapped, QFilter, path=Path.path)
        
    def getEntry(self, filterName, position):
        '''
        @see: IFilterService.getEntry
        '''
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        assert isinstance(position, int), 'Invalid position %s' % position
        
        sql = self.session().query(FilterEntryMapped).join(FilterMapped)
        sql = sql.filter(FilterMapped.Name == filterName).filter(FilterEntryMapped.Position == position)
        return sql.one()
        
    def getEntries(self, filterName):
        '''
        @see: IFilterService.getEntries
        '''
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        sql = self.session().query(FilterEntryMapped.Position).join(FilterMapped)
        sql = sql.filter(FilterMapped.Name == filterName)
        return iterateCollection(sql)
    
    def insert(self, filtre):
        '''
        @see: IFilterService.insert
        '''
        assert isinstance(filtre, FilterCreate), 'Invalid filter %s' % filtre

        dbFilter = FilterMapped()
        items, dbFilter.pathId = pathId(filtre.Path)
        dbFilter.Name = filtre.Name
        dbFilter.Target = filtre.Target
        dbFilter.Hash = generateHash(filtre)
        self.session().add(dbFilter)
        self.session().flush((dbFilter,))
        
        count = self.generateEntries(filtre, dbFilter.id, items)
        
        if filtre.Target is None: raise InputError(_('Expected a target entry position'), FilterCreate.Target)
        if filtre.Target < 1 or filtre.Target >= count:
            raise InputError(_('Invalid target entry position'), FilterCreate.Target)
        
        return filtre.Name
        
    def delete(self, name):
        '''
        @see: IFilterService.delete
        '''
        return deleteModel(FilterMapped, name)
    
    # ----------------------------------------------------------------
    
    def generateEntries(self, filtre, filterId, items):
        '''
        Generates the filter entries.
        
        @return: integer
            The total count of generated entries.
        '''
        assert isinstance(filtre, FilterCreate), 'Invalid filter %s' % filtre
        
        position = 1
        for item in items:
            if item != '*': continue
            entry = FilterEntryMapped()
            entry.Position = position
            entry.filterId = filterId
        
            # Handling a normal access.
            if not filtre.Types: raise InputError(_('Expected at least one type for first *'), FilterCreate.Types)
            assert isinstance(filtre.Types, dict), 'Invalid filter types %s' % filtre.Types
            if position not in filtre.Types:
                raise InputError(_('Expected a type for * at %(position)i'), FilterCreate.Types, position=position)
            
            entry.typeId = typeId(filtre.Types[position])
            self.session().add(entry)
            position += 1
        
        return position
