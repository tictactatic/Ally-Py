'''
Created on Aug 28, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Ioan v. Pocol

Implementation for handling ACL service.
'''

from ally.api.error import IdError
from ally.support.api.util_service import emptyCollection, modelId
from ally.support.sqlalchemy.mapper import MappedSupport
from ally.support.sqlalchemy.session import SessionSupport
from ally.support.sqlalchemy.util_service import buildQuery, iterateCollection
from security.api.right import QRight
from security.meta.right import RightMapped
from security.rbac.api.role import QRole, Role
from security.rbac.meta.rbac import RbacDefinition
from security.rbac.meta.rbac_intern import RoleNode, RbacRole, RbacRight, Rbac
from security.rbac.meta.role import RoleMapped
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import aliased
from sqlalchemy.sql.expression import and_

# --------------------------------------------------------------------

Child = RoleNode; Child = aliased(RoleNode)
Parent = RoleNode; Parent = aliased(RoleNode)
# Alias to use for the nodes.

class RbacServiceAlchemy(SessionSupport):
    '''
    Provides support for handling the RBAC data. By RBAC object is meant the object that has been configured to have the
    RBAC structure on it.
    '''
    
    def __init__(self, Rbac):
        '''
        Construct the RBAC service alchemy.
        
        @param Rbac: Base class
            The Rbac mapped class that organizes the RBAC structure.
        '''
        assert isinstance(Rbac, MappedSupport), 'Invalid mapped class %s' % Rbac
        assert issubclass(Rbac, RbacDefinition), 'Invalid Rbac class %s' % Rbac
        
        self.Rbac = Rbac
        self.RbacIdentifier = modelId(Rbac)
    
    def getRoles(self, identifier, q=None, **options):
        '''
        @see: IRbacPrototype.getRoles
        '''
        rbacId = self.findRbacId(identifier)
        if rbacId is None: return emptyCollection(**options)
            
        sql = self.session().query(RoleMapped.Name)
        sql = sql.join(Child, Child.roleId == RoleMapped.id)
        sql = sql.join(Parent, and_(Child.left > Parent.left, Child.right < Parent.right))
        sql = sql.join(RbacRole, and_(RbacRole.roleId == Parent.roleId, RbacRole.rbacId == rbacId))
        if q:
            assert isinstance(q, QRole), 'Invalid query %s' % q
            sql = buildQuery(sql, q, RoleMapped)
        return iterateCollection(sql, **options)
    
    def getRights(self, identifier, q=None, **options):
        '''
        @see: IRbacPrototype.getRights
        '''
        rbacId = self.findRbacId(identifier)
        if rbacId is None: return emptyCollection(**options)
        
        subq = self.session().query(RightMapped.Id)
        subq = subq.join(RbacRight, RbacRight.rightId == RightMapped.Id)
        subq = subq.join(Child, Child.roleId == RbacRight.rbacId)
        subq = subq.join(Parent, and_(Child.left >= Parent.left, Child.right <= Parent.right))
        subq = subq.join(RbacRole, and_(RbacRole.roleId == Parent.roleId, RbacRole.rbacId == rbacId))

        sql = self.session().query(RightMapped.Id)
        sql = sql.join(RbacRight, and_(RbacRight.rightId == RightMapped.Id, RbacRight.rbacId == rbacId))

        sql = sql.union(subq).distinct(RightMapped.Id).order_by(RightMapped.Id)
        
        if q:
            assert isinstance(q, QRight), 'Invalid query %s' % q
            sql = buildQuery(sql, q, RightMapped)
        return iterateCollection(sql, **options)

    def addRole(self, identifier, roleName):
        '''
        @see: IRbacPrototype.addRole
        '''
        assert isinstance(roleName, str), 'Invalid role name %s' % roleName
        
        try: roleId, = self.session().query(RoleMapped.id).filter(RoleMapped.Name == roleName)
        except NoResultFound: raise IdError(Role)
        rbacId = self.obtainRbacId(identifier)
        
        sql = self.session().query(RbacRole).filter(RbacRole.rbacId == rbacId).filter(RbacRole.roleId == roleId)
        if sql.count() > 0: return  # The role is already mapped to Rbac
        self.session().add(RbacRole(rbacId=rbacId, roleId=roleId))
        
    def remRole(self, identifier, roleName):
        '''
        @see: IRbacPrototype.addRole
        '''
        assert isinstance(roleName, str), 'Invalid role name %s' % roleName
        
        rbacId = self.findRbacId(identifier)
        if rbacId is None: return False
        
        sql = self.session().query(RbacRole).join(RoleMapped)
        sql = sql.filter(RbacRole.rbacId == rbacId).filter(RoleMapped.Name == roleName)
        try: rbacRole = sql.one()
        except NoResultFound: return False
        
        self.session().delete(rbacRole)
        return True
    
    def addRight(self, identifier, rightId):
        '''
        @see: IRbacPrototype.addRight
        '''
        assert isinstance(rightId, int), 'Invalid right id %s' % rightId
        
        rbacId = self.obtainRbacId(identifier)
        
        sql = self.session().query(RbacRight).filter(RbacRight.rbacId == rbacId).filter(RbacRight.rightId == rightId)
        if sql.count() > 0: return  # The right is already mapped to Rbac
        self.session().add(RbacRight(rbacId=rbacId, rightId=rightId))
        
    def remRight(self, identifier, rightId):
        '''
        @see: IRbacPrototype.remRight
        '''
        assert isinstance(rightId, int), 'Invalid right id %s' % rightId
        
        rbacId = self.findRbacId(identifier)
        if rbacId is None: return False
        
        sql = self.session().query(RbacRight)
        sql = sql.filter(RbacRight.rbacId == rbacId).filter(RbacRight.rightId == rightId)
        try: rbacRight = sql.one()
        except NoResultFound: return False
        
        self.session().delete(rbacRight)
        return True

    # ----------------------------------------------------------------
    
    def findRbacId(self, identifier):
        '''
        Find the Rbac id for the provided identifier. 
        
        @param identifier: object
            The RBAC object identifier to get the Rbac id.
        @return: integer|None
            The found Rbac id or None.
        '''
        sql = self.session().query(self.Rbac.rbacId)
        sql = sql.filter(self.RbacIdentifier == identifier)
        try: rbacId, = sql.one()
        except NoResultFound: return None
        return rbacId

    def obtainRbacId(self, identifier):
        '''
        Find or create the Rbac id for the provided identifier. 
        
        @param identifier: object
            The RBAC object identifier to get the Rbac id.
        @return: integer
            The found or created Rbac id.
        '''
        sql = self.session().query(self.Rbac)
        sql = sql.filter(self.RbacIdentifier == identifier)
        try: rbacContainer = sql.one()
        except NoResultFound: raise IdError(self.Rbac)
        assert isinstance(rbacContainer, RbacDefinition), 'Invalid Rbac container %s' % rbacContainer
        if rbacContainer.rbacId is None:
            rbac = Rbac()
            self.session().add(rbac)
            self.session().flush((rbac,))
            rbacContainer.rbacId = rbac.id
            
        return rbacContainer.rbacId
