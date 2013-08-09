'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for access group.
'''

from .access import Access
from .domain_acl import modelACL
from ally.api.config import service, call
from ally.api.type import Iter
from ally.support.api.entity_named import Entity, IEntityGetService

# --------------------------------------------------------------------

@modelACL
class Group(Entity):
    '''
    Defines the group of ACL access,
    '''
    Description = str

# --------------------------------------------------------------------

@service((Entity, Group))
class IGroupService(IEntityGetService):
    '''
    The ACL access group service provides the groups for organizing the accesses.
    '''
    
    @call
    def getGroups(self, access:Access=None) -> Iter(Group.Name):
        '''
        Provides the available filters.
        '''
