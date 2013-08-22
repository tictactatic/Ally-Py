'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL group.
'''

from ..api.group import IGroupService, Group
from ..meta.filter import FilterMapped
from ..meta.group import GroupMapped, AccessToGroup, FilterToEntry, \
    FilterToProperty
from acl.core.impl.filter_register import RegisterFilterEntry
from ally.api.error import IdError, InputError
from ally.container.ioc import injected
from ally.container.support import setup
from ally.internationalization import _
from ally.support.sqlalchemy.util_service import iterateCollection
from sql_alchemy.impl.entity import EntityNQServiceAlchemy, EntitySupportAlchemy
from sqlalchemy.orm.exc import NoResultFound
    
# --------------------------------------------------------------------

@injected
@setup(IGroupService, name='groupService')
class GroupServiceAlchemy(EntityNQServiceAlchemy, RegisterFilterEntry, IGroupService):
    '''
    Implementation for @see: IGroupService that provides the ACL groups.
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, GroupMapped)
        
    def getAll(self, accessId=None, **options):
        '''
        @see: IGroupService.getAll
        '''
        if accessId is None: return super().getAll(**options)
        sqlQuery = self.session().query(GroupMapped.Name).join(AccessToGroup)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId)
        return iterateCollection(sqlQuery, **options)
    
    def getAccesses(self, name, **options):
        '''
        @see: IGroupService.getAccesses
        '''
        sqlQuery = self.session().query(AccessToGroup.accessId).join(GroupMapped)
        sqlQuery = sqlQuery.filter(GroupMapped.Name == name)
        return iterateCollection(sqlQuery, **options)
    
    def getEntriesFiltered(self, name, accessId):
        '''
        @see: IGroupService.getEntriesFiltered
        '''
        sqlQuery = self.session().query(FilterToEntry.position).join(AccessToGroup).join(GroupMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == name)
        return iterateCollection(sqlQuery)
    
    def getEntryFilters(self, name, accessId, position):
        '''
        @see: IGroupService.getEntryFilters
        '''
        sqlQuery = self.session().query(FilterMapped.Name).join(FilterToEntry).join(AccessToGroup).join(GroupMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == name)
        sqlQuery = sqlQuery.filter(FilterToEntry.position == position)
        return iterateCollection(sqlQuery)
    
    def getPropertiesFiltered(self, name, accessId):
        '''
        @see: IGroupService.getPropertiesFiltered
        '''
        sqlQuery = self.session().query(FilterToProperty.name).join(AccessToGroup).join(GroupMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == name)
        return iterateCollection(sqlQuery)
    
    def getPropertyFilters(self, name, accessId, propName):
        '''
        @see: IGroupService.getPropertyFilters
        '''
        sqlQuery = self.session().query(FilterMapped.Name).join(FilterToProperty).join(AccessToGroup).join(GroupMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == name)
        sqlQuery = sqlQuery.filter(FilterToProperty.name == propName)
        return iterateCollection(sqlQuery)
        
    def addGroup(self, accessId, name):
        '''
        @see: IGroupService.addGroup
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(name, str), 'Invalid group name %s' % name
        
        try: group = self.session().query(GroupMapped).filter(GroupMapped.Name == name).one()
        except: raise IdError(Group)
        assert isinstance(group, GroupMapped), 'Invalid group %s' % group
        
        for accessId in self.iterateAllAccesses(accessId):
            sqlQuery = self.session().query(AccessToGroup)
            sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(AccessToGroup.groupId == group.id)
            if sqlQuery.count() > 0: continue
            
            accessToGroup = AccessToGroup()
            accessToGroup.accessId = accessId
            accessToGroup.groupId = group.id
    
            self.session().add(accessToGroup)
        return True
        
    def remGroup(self, accessId, name):
        '''
        @see: IGroupService.remGroup
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(name, str), 'Invalid group name %s' % name
        
        sqlQuery = self.session().query(AccessToGroup).join(GroupMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == name)
        try: accessToGroup = sqlQuery.one()
        except NoResultFound: return False
        
        self.session().delete(accessToGroup)
        return True

    def registerFilter(self, accessId, groupName, filterName, place=None):
        '''
        @see: IGroupService.registerFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(groupName, str), 'Invalid group name %s' % groupName
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        return self.assignFilterForAccess(accessId, filterName, place, groupName=groupName)
    
    def addEntryFilter(self, accessId, groupName, position, filterName):
        '''
        @see: IGroupService.addEntryFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(groupName, str), 'Invalid group name %s' % groupName
        assert isinstance(position, int), 'Invalid position %s' % position
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        filtre = self.checkEntryFilter(accessId, position, filterName)
        if filtre is None: raise InputError(_('Invalid filter for entry position'))
        return self.assignEntryFilter(accessId, groupName, position, filtre)

    def remEntryFilter(self, accessId, groupName, position, filterName):
        '''
        @see: IGroupService.remEntryFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(groupName, str), 'Invalid group name %s' % groupName
        assert isinstance(position, int), 'Invalid position %s' % position
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        sqlQuery = self.session().query(FilterToEntry).join(AccessToGroup).join(GroupMapped).join(FilterMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == groupName)
        sqlQuery = sqlQuery.filter(FilterToEntry.position == position).filter(FilterMapped.Name == filterName)
        try: filterEntry = sqlQuery.one()
        except NoResultFound: return False
        assert isinstance(filterEntry, FilterToEntry), 'Invalid filter to entry %s' % filterEntry
        
        self.session().delete(filterEntry)
        return True
    
    def addPropertyFilter(self, accessId, groupName, propName, filterName):
        '''
        @see: IGroupService.addPropertyFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(groupName, str), 'Invalid group name %s' % groupName
        assert isinstance(propName, str), 'Invalid property name %s' % propName
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        filtre = self.checkPropertyFilter(accessId, propName, filterName)
        if filtre is None: raise InputError(_('Invalid filter for property'))
        return self.assignPropertyFilter(accessId, groupName, propName, filtre)
        
    def remPropertyFilter(self, accessId, groupName, propName, filterName):
        '''
        @see: IGroupService.remPropertyFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(groupName, str), 'Invalid group name %s' % groupName
        assert isinstance(propName, str), 'Invalid property name %s' % propName
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        sqlQuery = self.session().query(FilterToProperty).join(AccessToGroup).join(GroupMapped).join(FilterMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == groupName)
        sqlQuery = sqlQuery.filter(FilterToProperty.name == propName).filter(FilterMapped.Name == filterName)
        try: filterProperty = sqlQuery.one()
        except NoResultFound: return False
        assert isinstance(filterProperty, FilterToProperty), 'Invalid filter to property %s' % filterProperty
        
        self.session().delete(filterProperty)
        return True

    # ----------------------------------------------------------------
    
    def assignEntryFilter(self, accessId, groupName, position, filtre, **keyargs):
        '''
        @see: RegisterFilterEntry.assignEntryFilter
        '''
        assert isinstance(position, int), 'Invalid position %s' % position
        assert isinstance(filtre, FilterMapped), 'Invalid filter %s' % filtre
        
        accessGroup = self.getAccessGroup(accessId, groupName)
        assert isinstance(accessGroup, AccessToGroup), 'Invalid access to group %s' % accessGroup
        
        sqlQuery = self.session().query(FilterToEntry)
        sqlQuery = sqlQuery.filter(FilterToEntry.accessGroupId == accessGroup.id).filter(FilterToEntry.filterId == filtre.id)
        sqlQuery = sqlQuery.filter(FilterToEntry.position == position)
        if sqlQuery.count() > 0: return  # Already assigned.

        filterToEntry = FilterToEntry()
        filterToEntry.accessGroupId = accessGroup.id
        filterToEntry.filterId = filtre.id
        filterToEntry.position = position
        
        self.session().add(filterToEntry)
        
    def assignPropertyFilter(self, accessId, groupName, name, filtre, **keyargs):
        '''
        @see: RegisterFilterEntry.assignPropertyFilter
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(filtre, FilterMapped), 'Invalid filter %s' % filtre
        
        accessGroup = self.getAccessGroup(accessId, groupName)
        assert isinstance(accessGroup, AccessToGroup), 'Invalid access to group %s' % accessGroup
        
        sqlQuery = self.session().query(FilterToProperty)
        sqlQuery = sqlQuery.filter(FilterToProperty.accessGroupId == accessGroup.id)
        sqlQuery = sqlQuery.filter(FilterToProperty.filterId == filtre.id).filter(FilterToProperty.name == name)
        if sqlQuery.count() > 0: return  # Already assigned.

        filterToProperty = FilterToProperty()
        filterToProperty.accessGroupId = accessGroup.id
        filterToProperty.filterId = filtre.id
        filterToProperty.name = name
        
        self.session().add(filterToProperty)
        
    # ----------------------------------------------------------------
    
    def getAccessGroup(self, accessId, name):
        '''
        Provides the access group for the provided arguments.
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(name, str), 'Invalid group name %s' % name
        sqlQuery = self.session().query(AccessToGroup).join(GroupMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == name)
        try: accessGroup = sqlQuery.one()
        except NoResultFound: raise InputError(_('Group not allowed for access'))
        return accessGroup
