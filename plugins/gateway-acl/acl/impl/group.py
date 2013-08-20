'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL group.
'''

from ..api.filter import Filter
from ..api.group import IGroupService, Group
from ..meta.filter import FilterMapped
from ..meta.group import GroupMapped, AccessToGroup, GroupToFilter
from ally.api.error import IdError, InputError
from ally.container.ioc import injected
from ally.container.support import setup
from ally.support.sqlalchemy.util_service import iterateCollection
from sql_alchemy.impl.entity import EntityNQServiceAlchemy, EntitySupportAlchemy
from sqlalchemy.orm.exc import NoResultFound
from ally.internationalization import _
from ..meta.access import AccessMapped
    
# --------------------------------------------------------------------

@injected
@setup(IGroupService, name='groupService')
class GroupServiceAlchemy(EntityNQServiceAlchemy, IGroupService):
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
    
    def getFilters(self, accessId, name, **options):
        '''
        @see: IGroupService.getFilters
        '''
        sqlQuery = self.session().query(FilterMapped.Name).join(GroupToFilter).join(AccessToGroup).join(GroupMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == name)
        return iterateCollection(sqlQuery, **options)
        
    def addGroup(self, accessId, name):
        '''
        @see: IGroupService.addGroup
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(name, str), 'Invalid group name %s' % name
        
        try: group = self.session().query(GroupMapped).filter(GroupMapped.Name == name).one()
        except: raise IdError(Group)
        assert isinstance(group, GroupMapped), 'Invalid group %s' % group
        
        sqlQuery = self.session().query(AccessToGroup)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(AccessToGroup.groupId == group.id)
        if sqlQuery.count() > 0: return True
        
        accessToGroup = AccessToGroup()
        accessToGroup.accessId = accessId
        accessToGroup.groupId = group.id

        self.session().add(accessToGroup)
        return True
    
    def addFilter(self, accessId, groupName, filterName, place=None):
        '''
        @see: IGroupService.addFilter
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(groupName, str), 'Invalid group name %s' % groupName
        assert isinstance(filterName, str), 'Invalid filter name %s' % filterName
        
        sqlQuery = self.session().query(AccessToGroup).join(GroupMapped)
        sqlQuery = sqlQuery.filter(AccessToGroup.accessId == accessId).filter(GroupMapped.Name == groupName)
        try: group = sqlQuery.one()
        except: raise InputError(_('Group not allowed for access'))
        assert isinstance(group, AccessToGroup), 'Invalid access to group %s' % group
        
        access = self.session().query(AccessMapped).filter(AccessMapped.Id == accessId).one()
        assert isinstance(access, AccessMapped), 'Invalid access %s' % access
        
        try: filtre = self.session().query(FilterMapped).filter(FilterMapped.Name == filterName).one()
        except: raise IdError(Filter)
        assert isinstance(filtre, FilterMapped), 'Invalid filter %s' % filtre
        
        sqlQuery = self.session().query(GroupToFilter)
        sqlQuery = sqlQuery.filter(GroupToFilter.groupId == group.id).filter(GroupToFilter.filterId == filtre.id)
        if sqlQuery.count() > 0: return True
        
        occurences = access.Types.count(filtre.Target)
        if occurences == 0: return False
        if occurences > 1: raise InputError(_('Filter matches multiple entries, a place is required to be specified'))
        
        groupToFilter = GroupToFilter()
        groupToFilter.groupId = group.id
        groupToFilter.filterId = filtre.id
        
        self.session().add(groupToFilter)
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
