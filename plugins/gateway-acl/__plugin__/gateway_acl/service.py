'''
Created on Jan 9, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for acl gateway.
'''
    
from ..gateway.service import gatewayMethodMerge, \
    updateAssemblyAnonymousGateways, assemblyAnonymousGateways
from __setup__.ally_core.resources import injectorAssembly, assemblyAssembler, \
    processMethod, register
from __setup__.ally_core_http.resources import \
    updateAssemblyAssemblerForHTTPCore, conflictResolve
from __setup__.ally_core_http.server import root_uri_resources
from ally.container import ioc, support
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from gateway.core.acl.impl.processor.gateway.root_uri import RootURIHandler

# --------------------------------------------------------------------

# The assembler processors
processFilter = indexAccess = filterTarget = support.notCreated  # Just to avoid errors

# The gateway processors
accessPermission = filterPermission = registerPermissionGateways = support.notCreated  # Just to avoid errors

# The management processors
handleAccess = handleMethod = handleGroup = handleFilter = support.notCreated  # Just to avoid errors

support.createEntitySetup('gateway.core.acl.impl.**.*')

# --------------------------------------------------------------------

@ioc.entity
def assemblyACLManagement() -> Assembly:
    ''' The assembly used for ACL management'''
    return Assembly('ACL management')

# --------------------------------------------------------------------

@ioc.entity
def rootURI() -> Handler:
    b = RootURIHandler()
    b.rootURI = root_uri_resources()
    return b

# --------------------------------------------------------------------

@ioc.after(updateAssemblyAnonymousGateways)
def updateAssemblyAnonymousGatewaysForAcl():
    assemblyAnonymousGateways().add(injectorAssembly(), rootURI(), accessPermission(), filterPermission(),
                                    registerPermissionGateways(), before=gatewayMethodMerge())
    
@ioc.after(updateAssemblyAssemblerForHTTPCore)
def updateAssemblyAssemblerForAcl():
    assemblyAssembler().add(processFilter(), before=processMethod())
    assemblyAssembler().add(filterTarget(), after=conflictResolve())
    assemblyAssembler().add(indexAccess())

@ioc.before(assemblyACLManagement)
def updateAssemblyACLManagement():
    assemblyACLManagement().add(injectorAssembly(), handleAccess(), handleMethod(), handleGroup(), handleFilter())

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
    print('ADDED:', groupService.addGroup('9F86DD04', 'GET', 'Anonymous'), 'GET:Security/Right/*')
    print('ADDED:', groupService.addGroup('9F86DD04', 'DELETE', 'Anonymous'), 'DELETE:Security/Right/*')

    assert isinstance(filterService, IFilterService)
    print('FILTERED:', filterService.addFilter('9F86DD04', 'GET', 'Anonymous', 'Filter1'), 'GET:Security/Right/*')
    print('FILTERED:', filterService.addFilter('9F86DD04', 'GET', 'Anonymous', 'Filter2'), 'GET:Security/Right/*')
    print('FILTERED:', filterService.addFilter('9F86DD04', 'DELETE', 'Anonymous', 'Filter1'), 'DELETE:Security/Right/*')
