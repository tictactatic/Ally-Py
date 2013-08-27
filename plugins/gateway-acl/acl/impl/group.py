'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL group.
'''

from ..api.group import IGroupService, QGroup
from ..meta.filter import FilterEntryMapped
from ..meta.group import GroupMapped, GroupAccess
from acl.core.impl.acl import AclServiceAlchemy
from ally.container.ioc import injected
from ally.container.support import setup
from sql_alchemy.impl.entity import EntityServiceAlchemy, EntitySupportAlchemy
    
# --------------------------------------------------------------------

@injected
@setup(IGroupService, name='groupService')
class GroupServiceAlchemy(EntityServiceAlchemy, AclServiceAlchemy, IGroupService):
    '''
    Implementation for @see: IGroupService that provides the ACL groups.
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, GroupMapped, QGroup)
        AclServiceAlchemy.__init__(self, GroupMapped, GroupAccess)
    
    def validateFilter(self, filterId):
        '''
        @see: AclServiceAlchemy.validateFilter
        '''
        assert isinstance(filterId, int), 'Invalid filter id %s' % filterId
        
        sql = self.session().query(FilterEntryMapped.id)
        sql = sql.filter(FilterEntryMapped.filterId == filterId)
        return sql.count() == 1  # Only the target entry is allowed
