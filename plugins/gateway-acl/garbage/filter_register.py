'''
Created on Aug 21, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation that provides the support for registering filters to entries.
'''


from acl.api.access import Entry, Access, Property
from acl.api.filter import Filter
from acl.meta.access import AccessMapped, EntryMapped, PropertyMapped
from acl.meta.filter import FilterMapped
from ally.api.error import IdError, InputError
from ally.internationalization import _
from ally.support.sqlalchemy.session import SessionSupport
from sqlalchemy.orm.exc import NoResultFound
import abc
    
# --------------------------------------------------------------------

class RegisterFilterEntry(SessionSupport, metaclass=abc.ABCMeta):
    '''
    Support implementation for handling the filter assignments.
    '''
    
    def iterateAllAccesses(self, accessId):
        '''
        Provides all accesses that are either shadows or shadowing for the provided access id.
        
        @param accessId: integer
            The access id to provide all shadow linked accesses for.
        @return: Iterable(integer)
            All accesses ids, this also includes the provided access id.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        try: access = self.session().query(AccessMapped).filter(AccessMapped.Id == accessId).one()
        except: raise IdError(Access)
        assert isinstance(access, AccessMapped), 'Invalid access %s' % access
        
        ids = [accessId]
        if access.Shadowing: ids.append(access.Shadowing)
        for id, in self.session().query(AccessMapped.Id).filter(AccessMapped.Shadowing == accessId).all(): ids.append(id)
        return ids
    
    def checkEntryFilter(self, accessId, position, filterName):
        '''
        Checks if the filer is compatible with the access and entry position.
        
        @param accessId: integer
            The access id to check the filter with.
        @param position: integer
            The position to check the filter at.
        @param filterName: string
            The filter name to check.
        @return: FilterMapped|None
            The mapped filter if the filter is compatible for access and entry position, None otherwise.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(position, int), 'Invalid position %s' % position
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        try: filtre = self.session().query(FilterMapped).filter(FilterMapped.Name == filterName).one()
        except NoResultFound: raise IdError(Filter)
        assert isinstance(filtre, FilterMapped), 'Invalid filter %s' % filtre
        
        sqlQuery = self.session().query(EntryMapped.typeId)
        sqlQuery = sqlQuery.filter(EntryMapped.accessId == accessId).filter(EntryMapped.Position == position)
        try: entryTypeId = sqlQuery.one()
        except NoResultFound: raise IdError(Entry)
        
        if entryTypeId == filtre.targetId: return filtre
        
    def checkPropertyFilter(self, accessId, name, filterName):
        '''
        Checks if the filer is compatible with the access and property name.
        
        @param accessId: integer
            The access id to check the filter with.
        @param name: string
            The property name to check the filter at.
        @param filterName: string
            The filter name to check.
        @return: FilterMapped|None
            The mapped filter if the filter is compatible for access and property name, None otherwise.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(name, str), 'Invalid property name %s' % name
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        try: filtre = self.session().query(FilterMapped).filter(FilterMapped.Name == filterName).one()
        except NoResultFound: raise IdError(Filter)
        assert isinstance(filtre, FilterMapped), 'Invalid filter %s' % filtre
        
        sqlQuery = self.session().query(PropertyMapped.typeId)
        sqlQuery = sqlQuery.filter(PropertyMapped.accessId == accessId).filter(PropertyMapped.Name == name)
        try: propTypeId = sqlQuery.one()
        except NoResultFound: raise IdError(Property)
        
        if propTypeId == filtre.targetId: return filtre

    # ----------------------------------------------------------------
    
    def assignFilterForAccess(self, accessId, filterName, place=None, **keyargs):
        '''
        Process the registration of the filter for the provided access.
        
        @param accessId: integer
            The access id to register the filter with.
        @param filterName: string
            The filter name to register.
        @param place: string|None
            The filter place pattern, this is used only if there are multiple possible occurrences for the filter in the access.
        @param keyargs: key arguments
            Addition key arguments to for the 'registerFilter' method.
        @return: boolean
            True if the filter is registered for access.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        try: access = self.session().query(AccessMapped).filter(AccessMapped.Id == accessId).one()
        except NoResultFound: raise IdError(Access)
        assert isinstance(access, AccessMapped), 'Invalid access %s' % access

        try: filtre = self.session().query(FilterMapped).filter(FilterMapped.Name == filterName).one()
        except NoResultFound: raise IdError(Filter)
        assert isinstance(filtre, FilterMapped), 'Invalid filter %s' % filtre
        
        sqlQuery = self.session().query(EntryMapped)
        sqlQuery = sqlQuery.filter(EntryMapped.accessId == accessId)
        entries = {entry.Position: entry for entry in sqlQuery.all()}
        
        filterEntries = []  # The compatible entries with the filter.
        for entry in entries.values():
            assert isinstance(entry, EntryMapped), 'Invalid entry %s' % entry
            if entry.typeId == filtre.targetId: filterEntries.append(entry)
        
        sqlQuery = self.session().query(PropertyMapped)
        sqlQuery = sqlQuery.filter(PropertyMapped.accessId == accessId)
        properties = {prop.Name: prop for prop in sqlQuery.all()}
        
        filterProperties = []  # The compatible properties with the filter.
        for prop in properties.values():
            assert isinstance(prop, PropertyMapped), 'Invalid property %s' % prop
            if prop.typeId == filtre.targetId: filterProperties.append(prop)
        
        if not filterEntries and not filterProperties: return False
        if len(filterEntries) + len(filterProperties) > 1:
            if place is None:
                raise InputError(_('Filter matches multiple entries and/or properties, a place is required to be specified'))
            filterEntries, filterProperties = self.determineFilterPlace(access, filtre, place, entries, properties)
        
        for entry in filterEntries:
            self.assignEntryFilter(accessId=accessId, position=entry.Position, filtre=filtre, **keyargs)
            if entry.Shadowing is not None:  # Registering the filter also for the shadowing entry.
                self.assignEntryFilter(accessId=access.Shadowing, position=entry.Shadowing, filtre=filtre, **keyargs)
                    
        for prop in filterProperties:
            self.assignPropertyFilter(accessId=accessId, name=prop.Name, filtre=filtre, **keyargs)
            if access.Shadowing is not None:  # Registering the filter also for the shadowing property.
                self.assignPropertyFilter(accessId=access.Shadowing, name=prop.Name, filtre=filtre, **keyargs)
        
        if access.Shadowing is None:
            # Registering the filter also for the shadows, if any, of this access.
            sqlQuery = self.session().query(EntryMapped).select_from(AccessMapped).join(EntryMapped)
            sqlQuery = sqlQuery.filter(AccessMapped.Shadowing == accessId)
            
            shadows = {}
            for sentry in sqlQuery.all():
                assert isinstance(sentry, EntryMapped), 'Invalid entry %s' % sentry
                sentries = shadows.get(sentry.accessId)
                if sentries is None: sentries = shadows[sentry.accessId] = {}
                sentries[sentry.Shadowing] = sentry.Position
            
            for shadowId, sentries in shadows.items():
                for entry in filterEntries:
                    self.assignEntryFilter(accessId=shadowId, position=sentries[entry.Position], filtre=filtre, **keyargs)
                for prop in filterProperties:
                    self.assignPropertyFilter(accessId=shadowId, name=prop.Name, filtre=filtre, **keyargs)
 
        return True
    
    # ----------------------------------------------------------------
    
    def determineFilterPlace(self, access, filtre, place, entries, properties):
        '''
        Determines the filter position and properties based on the provided place hint.
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
    
    # ----------------------------------------------------------------
    
    @abc.abstractmethod
    def assignEntryFilter(self, accessId, position, filtre, **keyargs):
        '''
        Register the filter at the provided entry position. This needs to be implemented to provide the registering for the
        filter based on the specific resource.
        This function will always receive the arguments as key arguments so position can change for arguments but not the
        names.
        
        @param accessId: integer
            The access id to register the filter with.
        @param position: integer
            The entry position to register the filter at.
        @param filtre: FilterMapped
            The filter to register
        @param keyargs: key arguments
            Addition key arguments.
        '''
        
    @abc.abstractmethod
    def assignPropertyFilter(self, accessId, name, filtre, **keyargs):
        '''
        Register the filter for the provided property name. This needs to be implemented to provide the registering for the
        filter based on the specific resource.
        This function will always receive the arguments as key arguments so position can change for arguments but not the
        names.
        
        @param accessId: integer
            The access id to register the filter with.
        @param name: string
            The property name to register the filter at.
        @param filtre: FilterMapped
            The filter to register
        @param keyargs: key arguments
            Addition key arguments.
        '''

