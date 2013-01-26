'''
Created on Jan 21, 2013

@package: security RBAC
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the setups for populating default data.
'''

from ..security.populate import populateRights
from ally.container import support, ioc
from ally.internationalization import NC_
from security.api.right import IRightService, Right
from security.rbac.api.rbac import IRoleService, QRole, Role
from security.rbac.core.spec import IRbacService

# --------------------------------------------------------------------

@ioc.entity
def rootRoleId():
    roleService = support.entityFor(IRoleService)
    assert isinstance(roleService, IRoleService)
    
    roles = roleService.getAll(limit=1, q=QRole(name='ROOT'))
    try: rootRole = next(iter(roles))
    except StopIteration:
        rootRole = Role()
        rootRole.Name = NC_('security role', 'ROOT')
        rootRole.Description = NC_('security role', 'Default role that provides access to all available roles and rights')
        return roleService.insert(rootRole)
    return rootRole.Id

@ioc.after(populateRights)
def populateRootRole():
    rightService = support.entityFor(IRightService)
    assert isinstance(rightService, IRightService)
    rbacService = support.entityFor(IRbacService)
    assert isinstance(rbacService, IRbacService)
    roleService = support.entityFor(IRoleService)
    assert isinstance(roleService, IRoleService)
    
    for right in rightService.getAll():
        assert isinstance(right, Right)
        roleService.assignRight(rootRoleId(), right.Id)
