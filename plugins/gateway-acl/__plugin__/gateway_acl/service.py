'''
Created on Jan 9, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for acl gateway.
'''
    
from ..gateway.service import registerMethodOverride, \
    updateAssemblyAnonymousGateways, assemblyAnonymousGateways
from __setup__.ally_core.resources import injectorAssembly, assemblyAssembler, \
    processMethod, register
from __setup__.ally_core_http.resources import \
    updateAssemblyAssemblerForHTTPCore, conflictResolve
from __setup__.ally_core_http.server import root_uri_resources
from ally.container import ioc, support
from ally.design.processor.assembly import Assembly

# --------------------------------------------------------------------

# The assembler processors
processFilter = indexAccess = filterTarget = support.notCreated  # Just to avoid errors

# The gateway processors
registerAccessGateways = support.notCreated  # Just to avoid errors

# The management processors
handleAccess = handleMethod = handleGroup = handleFilter = support.notCreated  # Just to avoid errors

support.createEntitySetup('gateway.core.acl.impl.**.*')

# --------------------------------------------------------------------

@ioc.entity
def assemblyACLManagement() -> Assembly:
    ''' The assembly used for ACL management'''
    return Assembly('ACL management')

# --------------------------------------------------------------------

@ioc.before(registerAccessGateways)
def configureRegisterAccessGateways():
    from gateway.core.acl.impl.processor.gateway.access_gateway import RegisterAccessGateways
    if isinstance(registerAccessGateways(), RegisterAccessGateways):
        # TODO: Gabriel: see in the future for a better link between configurations
        # We set the root URI configuration
        registerAccessGateways().root_uri = root_uri_resources()

@ioc.after(updateAssemblyAnonymousGateways)
def updateAssemblyAnonymousGatewaysForAcl():
    assemblyAnonymousGateways().add(injectorAssembly(), registerAccessGateways(), before=registerMethodOverride())
    
@ioc.after(updateAssemblyAssemblerForHTTPCore)
def updateAssemblyAssemblerForAcl():
    assemblyAssembler().add(processFilter(), before=processMethod())
    assemblyAssembler().add(filterTarget(), after=conflictResolve())
    assemblyAssembler().add(indexAccess())

@ioc.before(assemblyACLManagement)
def updateAssemblyACLManagement():
    assemblyACLManagement().add(injectorAssembly(), handleAccess(), handleMethod(), handleGroup(), handleFilter())

# TODO: Gabriel: rmove test data
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
    print('ADDED:', groupService.addGroup('00000000', 'GET', 'Anonymous'), ':/')
    print('ADDED:', groupService.addGroup('D4A00B30', 'GET', 'Anonymous'), ':ACL/Access/*/Method/*')
    
#    methodService.addMethod('00000000', 'Anonymous', 'GET')
#    methodService.addMethod('9780F2D6', 'Anonymous', 'GET')
#    methodService.addMethod('0CAF856D', 'Anonymous', 'GET')
#    
#    methodService.addMethod('D4CC4FC5', 'Anonymous', 'GET')
#    methodService.addMethod('D4CC4FC5', 'Anonymous', 'PUT')

    assert isinstance(filterService, IFilterService)
    print('FILTERED:', filterService.addFilter('00000000', 'GET', 'Anonymous', 'Dummy filter'), ':/')
    print('FILTERED:', filterService.addFilter('D4A00B30', 'GET', 'Anonymous', 'Dummy filter'), ':ACL/Access/*/Method/*')
