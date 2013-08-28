'''
Created on Jan 9, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for ACL.
'''
    
from ..gateway.service import updateAssemblyAnonymousGateways, \
    assemblyAnonymousGateways, gatewayMethodMerge, registerMethodOverride
from ..plugin.registry import registerService
from .database import binders
from acl.api.group import IGroupService, Group
from acl.core.impl.processor.gateway.acl_permission import \
    RegisterAclPermissionHandler
from ally.container import ioc, support, bind, app
from ally.container.support import entityFor
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

# The gateway processors
anonymousGroup = registerPermissionGateway = support.notCreated  # Just to avoid errors

SERVICES = 'acl.api.**.I*Service'

bind.bindToEntities('acl.impl.**.*Alchemy', 'acl.core.impl.processor.gateway.**.*Alchemy', binders=binders)
support.createEntitySetup('acl.impl.**.*', 'acl.core.impl.processor.gateway.**.*')
support.listenToEntities(SERVICES, listeners=registerService)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

@ioc.entity
def assemblyGroupGateways() -> Assembly:
    ''' The assembly used for generating the group gateways'''
    return Assembly('Group gateways')

# --------------------------------------------------------------------

@ioc.entity
def registerAclPermission() -> Handler:
    b = RegisterAclPermissionHandler()
    b.aclPermissionProvider = entityFor(IGroupService)
    return b

# --------------------------------------------------------------------

@ioc.after(updateAssemblyAnonymousGateways)
def updateAssemblyAnonymousGatewaysForAcl():
    assemblyAnonymousGateways().add(anonymousGroup(), registerAclPermission(), registerPermissionGateway(),
                                    before=gatewayMethodMerge())

@ioc.after(assemblyGroupGateways)
def updateAssemblyGroupGateways():
    assemblyGroupGateways().add(registerAclPermission(), registerPermissionGateway(), gatewayMethodMerge(),
                                registerMethodOverride())
    

    
# TODO: GAbriel: remove sample data
@app.populate(app.DEVEL)
def populateSamples():
    groupService = entityFor(IGroupService)
    assert isinstance(groupService, IGroupService)
    
    try:
        group = Group()
        group.Name = 'Anonymous'
        group.IsAnonymous = True
        groupService.insert(group)
    except: pass
    try:
        group = Group()
        group.Name = 'Test'
        #group.IsAnonymous = True
        groupService.insert(group)
    except: pass

    print('ACL/Access')
    groupService.addAcl(3232022005, 'Anonymous')
    groupService.addAcl(3232022005, 'Test')
    print('FILTER:', groupService.registerFilter(3232022005, 'Anonymous', 'Filter1', place='#Shadowing'))
    
    
#    print('ACL/Access/*')
#    print('ADDED:', groupService.addGroup(1285521629, 'Anonymous'))
#    print('FILTER:', groupService.registerFilter(1285521629, 'Anonymous', 'Filter1'))
#    
#    print('ADDED:', groupService.addGroup(1285521629, 'Test'))
    
    # Place sample
#    print('RBAC/Role/*/SubRole/*')
#    print('ADDED:', groupService.addGroup(2052129038, 'Test'))
#    print('FILTER:', groupService.registerFilter(2052129038, 'Test', 'Filter1', place='RBAC/Role/@/SubRole/* @Name@Prop'))
#    
#    print('RBAC/Role/*/Right/*')
#    print('ADDED:', groupService.addGroup(2405241041, 'Test'))
#    print('FILTER:', groupService.registerFilter(2405241041, 'Test', 'Filter1'))
#    
#    print('RBAC/Role/*/Right/*')
#    print('ADDED:', groupService.addGroup(1103728037, 'Test'))
#    print('FILTER:', groupService.registerFilter(1103728037, 'Test', 'Filter1'))
#    
#    # Shadow sample
#    print('ACL/Group/*/Access/*')
#    print('ADDED:', groupService.addGroup(2270841289, 'Anonymous'))
#    print('FILTER:', groupService.registerFilter(2270841289, 'Anonymous', 'Filter2'))
#    
#    print('ACL/Group/*/Access/*')
#    print('ADDED:', groupService.addGroup(2270841289, 'Test'))
#    print('FILTER:', groupService.registerFilter(2270841289, 'Test', 'Filter2'))
    

#    
#    print('ACL/Access')
#    print('ADDED:', groupService.addGroup(3232022005, 'Anonymous'))
#    print('FILTER:', groupService.registerFilter(3232022005, 'Anonymous', 'Filter1'))
#    
#    print('ACL/Access/*/Group/*/Entry/*/Filter/*')
#    print('ADDED:', groupService.addGroup(512347881, 'Anonymous'))
#    print('FILTER:', groupService.registerFilter(512347881, 'Anonymous', 'Filter1'))
#    
#    print('Gateway/Custom/*')
#    print('ADDED:', groupService.addGroup(903992123, 'Anonymous'))
#    print('FILTER:', groupService.registerFilter(903992123, 'Anonymous', 'Filter1'))
