'''
Created on Jan 9, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for acl gateway.
'''
    
from ..gateway.service import gatewayMethodMerge, \
    updateAssemblyAnonymousGateways, assemblyAnonymousGateways, \
    registerMethodOverride
from __setup__.ally_core.resources import injectorAssembly, assemblyAssembler, \
    processMethod, register
from __setup__.ally_core_http.resources import \
    updateAssemblyAssemblerForHTTPCore, conflictResolve
from __setup__.ally_core_http.server import root_uri_resources
from ally.container import ioc, support
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from gateway.core.acl.impl.processor.gateway.group_identifier import \
    GroupIdentifierHandler
from gateway.core.acl.impl.processor.gateway.root_uri import RootURIHandler
from gateway.core.acl.impl.processor.handle_group import GROUP_ANONYMOUS

# --------------------------------------------------------------------

# The assembler processors
processFilter = indexAccess = filterTarget = support.notCreated  # Just to avoid errors

# The gateway processors
accessPermission = filterPermission = registerPermissionGateways = support.notCreated  # Just to avoid errors

# The management processors
handleAccess = handleMethod = handleGroup = handleFilter = support.notCreated  # Just to avoid errors

support.createEntitySetup('gateway.core.acl.impl.**.*')

# --------------------------------------------------------------------

@ioc.config
def acl_groups_anonymous():
    ''' The ACL groups that are delivered for anonymous access.'''
    return [GROUP_ANONYMOUS]

# --------------------------------------------------------------------

@ioc.entity
def assemblyAccessManagement() -> Assembly:
    ''' The assembly used for access management'''
    return Assembly('ACL Access management')

@ioc.entity
def assemblyMethodManagement() -> Assembly:
    ''' The assembly used for method management'''
    return Assembly('ACL Method management')

@ioc.entity
def assemblyGroupManagement() -> Assembly:
    ''' The assembly used for group management'''
    return Assembly('ACL Group management')

@ioc.entity
def assemblyFilterManagement() -> Assembly:
    ''' The assembly used for filter management'''
    return Assembly('ACL Filter management')

@ioc.entity
def assemblyGroupGateways() -> Assembly:
    ''' The assembly used for generating ACL group gateways'''
    return Assembly('ACL Group gateways')

# --------------------------------------------------------------------

@ioc.entity
def rootURI() -> Handler:
    b = RootURIHandler()
    b.rootURI = root_uri_resources()
    return b

@ioc.entity
def anonymousGroupIdentifier() -> Handler:
    b = GroupIdentifierHandler()
    b.aclGroups = set(acl_groups_anonymous())
    return b

# --------------------------------------------------------------------

@ioc.before(assemblyAccessManagement)
def updateAssemblyAccessManagement():
    assemblyAccessManagement().add(injectorAssembly(), handleAccess())
    
@ioc.before(assemblyMethodManagement)
def updateAssemblyMethodManagement():
    assemblyMethodManagement().add(assemblyAccessManagement(), handleMethod())
    
@ioc.before(assemblyGroupManagement)
def updateAssemblyGroupManagement():
    assemblyGroupManagement().add(assemblyMethodManagement(), handleGroup())
    
@ioc.before(assemblyFilterManagement)
def updateAssemblyFilterManagement():
    assemblyFilterManagement().add(assemblyGroupManagement(), handleFilter())

# --------------------------------------------------------------------

@ioc.after(updateAssemblyAnonymousGateways)
def updateAssemblyAnonymousGatewaysForAcl():
    assemblyAnonymousGateways().add(injectorAssembly(), rootURI(), anonymousGroupIdentifier(), accessPermission(),
                                    filterPermission(), registerPermissionGateways(), before=gatewayMethodMerge())

@ioc.before(assemblyGroupGateways)
def updateAssemblyGroupGateways():
    assemblyGroupGateways().add(injectorAssembly(), rootURI(), accessPermission(), filterPermission(),
                                registerPermissionGateways(), gatewayMethodMerge(), registerMethodOverride())
  
@ioc.after(updateAssemblyAssemblerForHTTPCore)
def updateAssemblyAssemblerForAcl():
    assemblyAssembler().add(processFilter(), before=processMethod())
    assemblyAssembler().add(filterTarget(), after=conflictResolve())
    assemblyAssembler().add(indexAccess())


# TODO: Gabriel: remove test data
@ioc.start
def capture():
    global groupService, filterService
    from __plugin__.gateway import service
    from ally.container.support import entityFor
    from gateway.api.group import IGroupService
    from gateway.api.filter import IFilterService
    groupService = entityFor(IGroupService, group=service)
    filterService = entityFor(IFilterService, group=service)

@ioc.after(register)
def samples():
    from gateway.api.group import IGroupService
    from gateway.api.filter import IFilterService
    assert isinstance(groupService, IGroupService)
    print('ADDED:', groupService.addGroup('84611CBB', 'DELETE', 'Anonymous'), 'DELETE:RBAC/Role/*/SubRole/*')

    assert isinstance(filterService, IFilterService)
    print('FILTERED:', filterService.addFilter('84611CBB', 'DELETE', 'Anonymous', 'Filter1'), 'DELETE:RBAC/Role/*/SubRole/*')
