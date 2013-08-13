'''
Created on Dec 21, 2012

@package: security - role based access control
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for RBAC right.
'''

from .domain_rbac import modelRbac
from ally.api.config import query, service, call
from ally.api.criteria import AsLikeOrdered
from ally.api.option import SliceAndTotal  # @UnusedImport
from ally.api.type import Iter
from ally.support.api.entity_ided import Entity, QEntity, IEntityService
from security.api.right import Right, QRight

# --------------------------------------------------------------------

@modelRbac
class Rbac(Entity):
    '''
    Provides the base model that has role based access.
    '''

@modelRbac
class Role(Rbac):
    '''
    Provides the role related data.
    '''
    Name = str
    Description = str

# --------------------------------------------------------------------

@query(Role)
class QRole(QEntity):
    '''
    Query for role service
    '''
    name = AsLikeOrdered

# --------------------------------------------------------------------

@service((Entity, Role), (QEntity, QRole))
class IRoleService(IEntityService):
    '''
    Role model service API.
    '''
    
    @call(webName='ByName')
    def getByName(self, name:Role.Name) -> Role:
        '''
        Provides the role based on a provided name.
        '''
    
    @call(webName='Sub')
    def getRoles(self, roleId:Role, q:QRole=None, **options:SliceAndTotal) -> Iter(Role.Id):
        '''
        Provides the roles searched by the provided query.
        '''
        
    @call
    def getRights(self, roleId:Role, q:QRight=None, **options:SliceAndTotal) -> Iter(Right.Id):
        '''
        Provides the rights for the provided role id searched by the query.
        '''
    
    @call(webName='Sub')
    def assignRole(self, toRoleId:Role.Id, roleId:Role.Id):
        '''
        Assign to the role the other role. 
        '''
    
    @call(webName='Sub')
    def removeRole(self, toRoleId:Role.Id, roleId:Role.Id) -> bool:
        '''
        Remove from the role the other role. 
        '''
        
    @call
    def assignRight(self, roleId:Role.Id, rightId:Right.Id):
        '''
        Assign to the role the right. 
        '''
    
    @call
    def removeRight(self, roleId:Role.Id, rightId:Right.Id) -> bool:
        '''
        Remove from the role the right. 
        '''
