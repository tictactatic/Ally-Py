'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL group.
'''

from ..api.group import IGroupService, QGroup
from ..meta.group import GroupMapped, GroupAccess, GroupCompensate
from acl.api.group import Group
from acl.core.impl.acl import AclServiceAlchemy
from acl.core.impl.compensate import CompensateServiceAlchemy
from acl.core.spec import signature
from ally.container.ioc import injected
from ally.container.support import setup
from sql_alchemy.impl.entity import EntityServiceAlchemy, EntitySupportAlchemy
    
# --------------------------------------------------------------------

@injected
@setup(IGroupService, name='groupService')
class GroupServiceAlchemy(EntityServiceAlchemy, AclServiceAlchemy, CompensateServiceAlchemy, IGroupService):
    '''
    Implementation for @see: IGroupService that provides the ACL groups.
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, GroupMapped, QGroup)
        AclServiceAlchemy.__init__(self, GroupMapped, GroupAccess)
        CompensateServiceAlchemy.__init__(self, GroupMapped, GroupAccess, GroupCompensate,
                                          signatures={signature(Group.Name): lambda identifier: identifier})
