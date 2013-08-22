'''
Created on Jan 9, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for ACL.
'''
    
from ..gateway.service import updateAssemblyAnonymousGateways, \
    assemblyAnonymousGateways, gatewayMethodMerge
from ..plugin.registry import addService
from .db_acl import bindACLSession, bindACLValidations
from acl.api.group import IGroupService, Group
from acl.core.impl.processor.gateway.group_specifier import \
    GroupSpecifierHandler
from ally.container import ioc, support, bind, app
from ally.container.support import entityFor
from ally.design.processor.handler import Handler
from itertools import chain

# --------------------------------------------------------------------

GROUP_ANONYMOUS = 'Anonymous'
# The anonymous group name.

# --------------------------------------------------------------------

# The gateway processors
registerGroupPermission = registerPermissionGateway = support.notCreated  # Just to avoid errors

SERVICES = 'acl.api.**.I*Service'
@ioc.entity
def binders(): return [bindACLSession]
@ioc.entity
def bindersService(): return list(chain((bindACLValidations,), binders()))

bind.bindToEntities('acl.impl.**.*Alchemy', 'acl.core.impl.processor.gateway.**.*Alchemy', binders=binders)
support.createEntitySetup('acl.impl.**.*', 'acl.core.impl.processor.gateway.**.*')
support.listenToEntities(SERVICES, listeners=addService(bindersService))
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

@ioc.config
def acl_groups_anonymous():
    ''' The ACL groups that are delivered for anonymous access.'''
    return [GROUP_ANONYMOUS, 'Test']  # TODO: Gabriel: remove sample data

# --------------------------------------------------------------------

@ioc.entity
def anonymousGroupSpecifier() -> Handler:
    b = GroupSpecifierHandler()
    b.groups = acl_groups_anonymous()
    return b

# --------------------------------------------------------------------

@ioc.after(updateAssemblyAnonymousGateways)
def updateAssemblyAnonymousGatewaysForAcl():
    assemblyAnonymousGateways().add(anonymousGroupSpecifier(), registerGroupPermission(), registerPermissionGateway(),
                                    before=gatewayMethodMerge())
    
@app.populate(app.DEVEL)
def populateGroupAnonymous():
    groupService = entityFor(IGroupService)
    assert isinstance(groupService, IGroupService)
    
    try: groupService.getById(GROUP_ANONYMOUS)
    except:
        group = Group()
        group.Name = GROUP_ANONYMOUS
        group.Description = 'This group contains the services that can be accessed by anyone'
        groupService.insert(group)
        
# TODO: GAbriel: remove sample data
@ioc.after(populateGroupAnonymous)
def populateSamples():
    groupService = entityFor(IGroupService)
    assert isinstance(groupService, IGroupService)
    
    # TODO: Gabriel: Implement also Model ACL
    try:
        group = Group()
        group.Name = 'Test'
        groupService.insert(group)
    except: pass

    print('ACL/Access')
    print('ADDED:', groupService.addGroup(3232022005, 'Anonymous'))
    print('FILTER:', groupService.registerFilter(3232022005, 'Anonymous', 'Filter1', place='#Shadowing'))
    
#    print('ACL/Access/*')
#    print('ADDED:', groupService.addGroup(1285521629, 'Anonymous'))
#    print('FILTER:', groupService.registerFilter(1285521629, 'Anonymous', 'Filter1'))
#    
#    print('ADDED:', groupService.addGroup(1285521629, 'Test'))
    
    # TODO: filter place pattern with model: RBAC/Role/@/SubRole/*#Name,Prop
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
