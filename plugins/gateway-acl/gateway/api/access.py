'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for service access.
'''

from .domain_acl import modelACL
from ally.api.config import service, call, query, INSERT
from ally.api.criteria import AsLikeOrdered, AsEqualOrdered
from ally.api.type import Iter

# --------------------------------------------------------------------

@modelACL(id='Name')
class Group:
    '''
    Defines the group of ACL access,
    '''
    Name = str
    Description = str

@modelACL(id='Id')
class Access:
    '''
    Defines an access entry based on a URI pattern and method.
    '''
    Id = int
    Pattern = str
    Method = str

# --------------------------------------------------------------------

@query(Access)
class QAccess:
    '''
    Query for access entities.
    '''
    pattern = AsLikeOrdered
    method = AsEqualOrdered

# --------------------------------------------------------------------

@service
class IAccessService:
    '''
    The ACL access service provides the means of setting up the access control layer for services.
    '''
    
    @call
    def getGroups(self) -> Iter(Group):
        '''
        Provides all the ACL groups.
        '''
    
    @call(method=INSERT)
    def allow(self, name:Group.Name, access:Access) -> Access.Id:
        '''
        Setup access for the provided access data.
        '''
        
    @call
    def remove(self, name:Group, id:Access) -> bool:
        '''
        Removes the access for the provided id.
        '''
