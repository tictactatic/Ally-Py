'''
Created on Dec 21, 2012

@package: security - role based access control
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

RBAC implementation for roles.
'''

from ..api.rbac import IRoleService, QRole
from ..core.spec import IRbacService
from ..meta.rbac import RoleMapped
from ..meta.rbac_intern import RbacRight
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.support.sqlalchemy.util_service import buildQuery, iterateCollection
from security.api.right import QRight
from security.meta.right import RightMapped
from sql_alchemy.impl.entity import EntityServiceAlchemy

# --------------------------------------------------------------------
    
@injected
@setup(IRoleService, name='roleService')
class RoleServiceAlchemy(EntityServiceAlchemy, IRoleService):
    '''
    Implementation for @see: IRoleService
    '''
    
    rbacService = IRbacService; wire.entity('rbacService')
    # Rbac service to use for complex role operations.
    
    def __init__(self):
        assert isinstance(self.rbacService, IRbacService), 'Invalid rbac service %s' % self.rbacService
        EntityServiceAlchemy.__init__(self, RoleMapped, QRole)
        
    def getByName(self, name):
        '''
        @see: IRoleService.getByName
        '''
        return self.session().query(RoleMapped).filter(RoleMapped.Name == name).one()
    
    def getRoles(self, roleId, q=None, **options):
        '''
        @see: IRoleService.getRoles
        '''
        sqlQuery = self.rbacService.rolesForRbacSQL(roleId, self.session().query(RoleMapped.Id))
        if q is not None:
            assert isinstance(q, QRole), 'Invalid query %s' % q
            sqlQuery = buildQuery(sqlQuery, q, RoleMapped)
        return iterateCollection(sqlQuery, **options)
    
    def getRights(self, roleId, q=None, **options):
        '''
        @see: IRoleService.getRights
        '''
        sqlQuery = self.rbacService.rightsForRbacSQL(roleId, self.session().query(RightMapped.Id))
        if q is not None:
            assert isinstance(q, QRight), 'Invalid query %s' % q
            sqlQuery = buildQuery(sqlQuery, q, RightMapped)
        return iterateCollection(sqlQuery, **options)
    
    def insert(self, role):
        '''
        @see: EntityCRUDServiceAlchemy.insert
        '''
        roleId = super().insert(role)
        self.rbacService.mergeRole(roleId)
        return roleId
    
    def assignRole(self, toRoleId, roleId):
        '''
        @see: IRoleService.assignRole
        '''
        self.rbacService.assignRole(roleId, toRoleId)

    def removeRole(self, toRoleId, roleId):
        '''
        @see: IRoleService.removeRole
        '''
        return self.rbacService.unassignRole(roleId, toRoleId)
    
    def assignRight(self, roleId, rightId):
        '''
        @see: IRoleService.assignRole
        '''
        sql = self.session().query(RbacRight).filter(RbacRight.rbac == roleId).filter(RbacRight.right == rightId)
        if sql.count() > 0: return  # The right is already mapped to role
        self.session().add(RbacRight(rbac=roleId, right=rightId))
        
    def removeRight(self, roleId, rightId):
        '''
        @see: IRoleService.removeRight
        '''
        sql = self.session().query(RbacRight).filter(RbacRight.rbac == roleId).filter(RbacRight.right == rightId)
        return sql.delete() > 0

# --------------------------------------------------------------------
