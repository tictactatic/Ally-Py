'''
Created on Aug 26, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for category service.
'''

from ..spec import ICategoryService
from acl.api.access import Access, Entry, Property
from acl.api.filter import Filter
from acl.meta import filter
from acl.meta.access import EntryMapped, PropertyMapped, AccessMapped
from acl.meta.category import Category, CategoryAccess, CAEntryFilter, \
    CAPropertyFilter
from acl.meta.filter import FilterMapped
from ally.api.error import IdError, InputError
from ally.container.support import setup
from ally.internationalization import _
from ally.support.sqlalchemy.session import SessionSupport
from sqlalchemy.orm.exc import NoResultFound

# --------------------------------------------------------------------

@setup(ICategoryService, name='categoryService')
class CategoryServiceAlchemy(ICategoryService, SessionSupport):
    '''
    Implementation for @see: ICategoryService.
    '''
    
    def categoriesForAccessSQL(self, accessId, sql=None):
        '''
        @see: ICategoryService.categoriesForAccessSQL
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        sql = sql or self.session().query(CategoryAccess.categoryId)
        sql = sql.filter(CategoryAccess.accessId == accessId)
        return sql

    def accessesForSQL(self, sql=None, **data):
        '''
        @see: ICategoryService.accessesForSQL
        '''
        return self.identifyCategory(sql or self.session().query(CategoryAccess.accessId), data)
    
    def entriesFilteredForSQL(self, accessId, sql=None, **data):
        '''
        @see: ICategoryService.entriesFilteredForSQL
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        sql = sql or self.session().query(EntryMapped.Position)
        sql = sql.join(CAEntryFilter).join(CategoryAccess)
        sql = sql.filter(CategoryAccess.accessId == accessId)
        return self.identifyCategory(sql, data)
    
    def entryFiltersForSQL(self, accessId, entryPosition, sql=None, **data):
        '''
        @see: ICategoryService.entryFiltersForSQL
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(entryPosition, int), 'Invalid entry position %s' % entryPosition
        
        sql = sql or self.session().query(FilterMapped.Name)
        sql = sql.join(CAEntryFilter).join(EntryMapped).join(CategoryAccess)
        sql = sql.filter(CategoryAccess.accessId == accessId).filter(EntryMapped.Position == entryPosition)
        return self.identifyCategory(sql, data)
    
    def propertiesFilteredForSQL(self, accessId, sql=None, **data):
        '''
        @see: ICategoryService.propertiesFilteredForSQL
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        sql = sql or self.session().query(PropertyMapped.Name)
        sql = sql.join(CAPropertyFilter).join(CategoryAccess)
        sql = sql.filter(CategoryAccess.accessId == accessId)
        return self.identifyCategory(sql, data)
    
    def propertyFiltersForSQL(self, accessId, propertyName, sql=None, **data):
        '''
        @see: ICategoryService.propertyFiltersForSQL
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(propertyName, str), 'Invalid property name %s' % propertyName
        
        sql = sql or self.session().query(FilterMapped.Name)
        sql = sql.join(CAPropertyFilter).join(PropertyMapped).join(CategoryAccess)
        sql = sql.filter(CategoryAccess.accessId == accessId).filter(PropertyMapped.Name == propertyName)
        return self.identifyCategory(sql, data)
    
    def categoryAdd(self, accessId, categoryId):
        '''
        @see: ICategoryService.categoryAdd
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(categoryId, int), 'Invalid category id %s' % categoryId
        
        try: access = self.session().query(AccessMapped).filter(AccessMapped.Id == accessId).one()
        except: raise IdError(Access)
        assert isinstance(access, AccessMapped), 'Invalid access %s' % access
        
        ids = [accessId]
        if access.Shadowing: ids.append(access.Shadowing)
        for id, in self.session().query(AccessMapped.Id).filter(AccessMapped.Shadowing == accessId).all(): ids.append(id)
    
        for accessId in ids:
            sql = self.session().query(CategoryAccess)
            sql = sql.filter(CategoryAccess.accessId == accessId).filter(CategoryAccess.categoryId == categoryId)
            if sql.count() > 0: continue
            
            categoryAccess = CategoryAccess()
            categoryAccess.accessId = accessId
            categoryAccess.categoryId = categoryId
    
            self.session().add(categoryAccess)
            
    def categoryRemove(self, accessId, **data):
        '''
        @see: ICategoryService.categoryRemove
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        sql = self.session().query(CategoryAccess).filter(CategoryAccess.accessId == accessId)
        sql = self.identifyCategory(sql, data)
        try: categoryAccess = sql.one()
        except NoResultFound: return False
        
        self.session().delete(categoryAccess)
        return True
    
    def entryFilterAdd(self, accessId, entryPosition, filterName, **data):
        '''
        @see: ICategoryService.entryFilterAdd
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(entryPosition, int), 'Invalid entry position %s' % entryPosition
        assert isinstance(filterName, int), 'Invalid filter name%s' % filterName
        
        filterId = self.checkEntryFilter(accessId, entryPosition, filterName)
        if filterId is None: raise InputError(_('Invalid filter for entry position'))
        return self.assignEntryFilter(accessId, entryPosition, filterId, data)
    
    def entryFilterRemove(self, accessId, entryPosition, filterName, **data):
        '''
        @see: ICategoryService.entryFilterRemove
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(entryPosition, int), 'Invalid entry position %s' % entryPosition
        assert isinstance(filterName, int), 'Invalid filter name%s' % filterName
        
        sql = self.session().query(CAEntryFilter).join(EntryMapped).join(CategoryAccess).join(FilterMapped)
        sql = sql.filter(CategoryAccess.accessId == accessId)
        sql = sql.filter(EntryMapped.Position == entryPosition).filter(FilterMapped.Name == filterName)
        sql = self.identifyCategory(sql, data)
        try: entryFilter = sql.one()
        except NoResultFound: return False
        
        self.session().delete(entryFilter)
        return True
    
    def propertyFilterAdd(self, accessId, propertyName, filterName, **data):
        '''
        @see: ICategoryService.propertyFilterAdd
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(propertyName, str), 'Invalid property name %s' % propertyName
        assert isinstance(filterName, int), 'Invalid filter name%s' % filterName
        
        filterId = self.checkPropertyFilter(accessId, propertyName, filterName)
        if filterId is None: raise InputError(_('Invalid filter for property name'))
        return self.assignPropertyFilter(accessId, propertyName, filterId, data)
    
    def propertyFilterRemove(self, accessId, propertyName, filterName, **data):
        '''
        @see: ICategoryService.propertyFilterRemove
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(propertyName, str), 'Invalid property name %s' % propertyName
        assert isinstance(filterName, int), 'Invalid filter name%s' % filterName
        
        sql = self.session().query(CAPropertyFilter).join(PropertyMapped).join(CategoryAccess).join(FilterMapped)
        sql = sql.filter(CategoryAccess.accessId == accessId)
        sql = sql.filter(PropertyMapped.Name == propertyName).filter(FilterMapped.Name == filterName)
        sql = self.identifyCategory(sql, data)
        try: propertyFilter = sql.one()
        except NoResultFound: return False
        
        self.session().delete(propertyFilter)
        return True
    
    def assignFilterForAccess(self, accessId, filterName, place=None, **data):
        '''
        @see: ICategoryService.assignFilterForAccess
        '''
        # TODO: implement
    
    # --------------------------------------------------------------------
    
    def identifyCategory(self, sql, data):
        '''
        Used for patching sql in order to filter the category provided in data.
        For this implementation is a must that 'CategoryAccess' is in the sql.
        '''
        assert isinstance(data, dict), 'Invalid data %s' % data
        assert 'categoryId' in data, 'Expected the categoryId key argument in %s' % data
        
        return sql.filter(CategoryAccess.categoryId == data['categoryId'])
    
    # --------------------------------------------------------------------
    
    def categoryAccessId(self, accessId, data):
        '''
        Provides the category access id.
        
        @param accessId: integer
            The access id.
        @param data: key arguments
            The data used to identify the category, by default a 'categoryId' is expected.
        '''
        sql = self.session().query(CategoryAccess.id).filter(CategoryAccess.accessId == accessId)
        sql = self.identifyCategory(sql, data)
        try: categoryAccessId, = sql.one()
        except NoResultFound: raise InputError(_('Access not allowed'))
        return categoryAccessId
    
    def checkEntryFilter(self, accessId, entryPosition, filterName):
        '''
        Checks if the filter is compatible with the access and entry position.
        
        @param accessId: integer
            The access id to check the filter with.
        @param entryPosition: integer
            The entry position to check the filter at.
        @param filterName: string
            The filter name to check.
        @return: integer|None
            The mapped filter id if the filter is compatible for access and entry position, None otherwise.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(entryPosition, int), 'Invalid entry position %s' % entryPosition
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        sql = self.session().query(FilterMapped.id).join(filter.EntryMapped)
        sql = sql.join(EntryMapped, filter.EntryMapped.typeId == EntryMapped.typeId)
        sql = sql.filter(FilterMapped.Target == filter.EntryMapped.id)
        sql = sql.filter(EntryMapped.accessId == accessId).filter(EntryMapped.Position == entryPosition)
        try: filterId, = sql.one()
        except NoResultFound: return
        return filterId
        
    def checkPropertyFilter(self, accessId, propertyName, filterName):
        '''
        Checks if the filter is compatible with the access and property name.
        
        @param accessId: integer
            The access id to check the filter with.
        @param propertyName: string
            The property name to check the filter at.
        @param filterName: string
            The filter name to check.
        @return: integer|None
            The mapped filter id if the filter is compatible for access and property name, None otherwise.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(propertyName, str), 'Invalid property name %s' % propertyName
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        sql = self.session().query(FilterMapped.id).join(filter.EntryMapped)
        sql = sql.join(PropertyMapped, filter.EntryMapped.typeId == PropertyMapped.typeId)
        sql = sql.filter(FilterMapped.Target == filter.EntryMapped.id)
        sql = sql.filter(PropertyMapped.accessId == accessId).filter(PropertyMapped.Name == propertyName)
        try: propertyId, = sql.one()
        except NoResultFound: return
        return propertyId
        
    def assignEntryFilter(self, accessId, entryPosition, filterId, data):
        '''
        Register the filter at the provided entry position.
        
        @param accessId: integer
            The access id to register the filter with.
        @param entryPosition: integer
            The entry position to register the filter at.
        @param filterId: integer
            The filter id to register
        @param data: key arguments
            The data used to identify the category, by default a 'categoryId' is expected.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(entryPosition, int), 'Invalid position %s' % entryPosition
        assert isinstance(filterId, int), 'Invalid filter id %s' % filterId
        
        sql = self.session().query(EntryMapped.id).join(AccessMapped)
        sql = sql.filter(AccessMapped.Id == accessId).filter(EntryMapped.Position == entryPosition)
        try: entryId = sql.one()
        except NoResultFound: raise IdError(Entry.Position)
        
        categoryAccessId = self.categoryAccessId(accessId, data)
        
        sql = self.session().query(CAEntryFilter)
        sql = sql.filter(CAEntryFilter.categoryAccessId == categoryAccessId).filter(CAEntryFilter.filterId == filterId)
        sql = sql.filter(CAEntryFilter.entryId == entryId)
        if sql.count() > 0: return  # Already assigned.

        entryFilter = CAEntryFilter()
        entryFilter.categoryAccessId = categoryAccessId
        entryFilter.entryId = entryId
        entryFilter.filterId = filterId
        
        self.session().add(entryFilter)
        
    def assignPropertyFilter(self, accessId, propertyName, filterId, data):
        '''
        Register the filter at the provided property name.
        
        @param accessId: integer
            The access id to register the filter with.
        @param propertyName: string
            The property name to register the filter at.
        @param filterId: integer
            The filter id to register
        @param data: key arguments
            The data used to identify the category, by default a 'categoryId' is expected.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(propertyName, str), 'Invalid property name %s' % propertyName
        assert isinstance(filterId, int), 'Invalid filter id %s' % filterId
        
        sql = self.session().query(PropertyMapped.id).join(AccessMapped)
        sql = sql.filter(AccessMapped.Id == accessId).filter(PropertyMapped.Name == propertyName)
        try: propertyId = sql.one()
        except NoResultFound: raise IdError(Property.Name)
        
        categoryAccessId = self.categoryAccessId(accessId, data)
        
        sql = self.session().query(CAPropertyFilter)
        sql = sql.filter(CAPropertyFilter.categoryAccessId == categoryAccessId).filter(CAPropertyFilter.filterId == filterId)
        sql = sql.filter(CAPropertyFilter.propertyId == propertyId)
        if sql.count() > 0: return  # Already assigned.

        propertyFilter = CAPropertyFilter()
        propertyFilter.categoryAccessId = categoryAccessId
        propertyFilter.propertyId = propertyId
        propertyFilter.filterId = filterId
        
        self.session().add(propertyFilter)
        
    def determineFilterPlace(self, access, filtre, place, entries, properties):
        '''
        Determines the filter position and properties based on the provided place hint.
        
        @param access: AccessMapped
            The access to determine the place for.
        @param filtre: FilterMapped
            The filter to determine place for.
        @param place: string
            The place pattern.
        @param entries: dictionary{integer: EntryMapped}
            The entries for access indexed by position.
        @param properties: dictionary{string: PropertyMapped}
            The properties for access indexed by name.
        @return: tuple(dictionary{}, dictionary{})
        '''
        assert isinstance(access, AccessMapped), 'Invalid access %s' % access
        assert isinstance(filtre, FilterMapped), 'Invalid filter %s' % filtre
        assert isinstance(place, str), 'Invalid place %s' % place
        assert isinstance(entries, dict), 'Invalid entries %s' % entries
        assert isinstance(properties, dict), 'Invalid properties %s' % properties
        
        place = place.strip().split('#', 1)
        if len(place) > 1: placeEntries, placeProperties = place
        else: placeEntries, placeProperties = place[0], ''
        
        filterEntries, filterProperties = [], []
        
        try:
            if placeEntries:
                markers, items = placeEntries.strip().strip('/').split('/'), access.Path.split('/')
            
                if len(items) == len(markers):
                    position = 0
                    for mark, item in zip(markers, items):
                        if item == '*':
                            position += 1
                            if mark == '@':
                                entry = entries.get(position)
                                if entry.typeId != filtre.targetId:
                                    raise InputError(_('Invalid filter path place preference at position %(position)s, '
                                                       'it is not compatible with the filter'), position=position)
                                filterEntries.append(entry)
                                continue
                            
                        if mark != item:
                            raise InputError(_('Invalid filter path place item %(item)s, needs to match %(path)s'),
                                             item=mark, path=access.Path)
                else:
                    raise InputError(_('Invalid filter path place, needs to match %(path)s'), path=access.Path)
                
            if placeProperties:
                for name in placeProperties.strip().split(','):
                    prop = properties.get(name.strip())
                    if prop is None: raise InputError(_('Unknown filter property place \'%(name)s\''), name=name)
                    assert isinstance(prop, PropertyMapped), 'Invalid property %s' % prop
                    if prop.typeId != filtre.targetId:
                        raise InputError(_('Invalid filter property place %(name)s, it is not compatible '
                                           'with the filter'), name=name)
                    filterProperties.append(prop)
                    
            if not filterEntries and not filterProperties:
                raise InputError(_('Invalid filter place \'%(place)s\' has not valid location preference'), place=place)
                
        except InputError as e:
            assert isinstance(e, InputError)
            # We generate a samples for place
            position, items, inPath, props = 0, [], False, []
            for item in access.Path.split('/'):
                if item == '*':
                    position += 1
                    entry = entries.get(position)
                    if entry.typeId == filtre.targetId:
                        items.append('@')
                        inPath = True
                        continue
                items.append(item)
                
            for name, prop in properties.items():
                if prop.typeId == filtre.targetId: props.append(name)
            
            if inPath: place = '/'.join(items)
            else: place = ''
            if props: place = '%s#%s' % (place, ','.join(props))
            
            e.update(_('Use place \'%(sample)s\' in order to add the filter on all available places'), sample=place)
            raise e
                
        return filterEntries, filterProperties
