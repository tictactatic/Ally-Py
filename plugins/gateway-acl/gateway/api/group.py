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
from .method import Method
from ally.api.config import service, call
from ally.api.type import Iter
from ally.support.api.entity_named import Entity, IEntityGetService, \
    IEntityFindService

# --------------------------------------------------------------------

@modelACL
class Group(Entity):
    '''
    Defines the group of ACL access,
    '''
    Description = str

# --------------------------------------------------------------------

@service((Entity, Group))
class IGroupService(IEntityGetService, IEntityFindService):
    '''
    The ACL access group service provides the groups for organizing the accesses.
    '''
        
    @call
    def getAllowed(self, access:Access.Name, method:Method) -> Iter(Group.Name):
        '''
        Provides the allowed groups for method in access.
        '''
    
    @call
    def addGroup(self, access:Access.Name, method:Method.Name, group:Group.Name) -> bool:
        '''
        Adds a new group for the access method.
        '''
        
    @call
    def removeGroup(self, access:Access, method:Method, group:Group) -> bool:
        '''
        Removes the group for the access method.
        '''
