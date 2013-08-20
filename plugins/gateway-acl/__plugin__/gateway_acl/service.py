'''
Created on Jan 9, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for ACL.
'''
    
from ..plugin.registry import addService
from .db_acl import bindACLSession, bindACLValidations
from acl.api.group import IGroupService, Group
from ally.container import ioc, support, bind, app
from ally.container.support import entityFor
from itertools import chain

# --------------------------------------------------------------------

GROUP_ANONYMOUS = 'Anonymous'
# The anonymous group name.

# --------------------------------------------------------------------

SERVICES = 'acl.api.**.I*Service'
@ioc.entity
def binders(): return [bindACLSession]
@ioc.entity
def bindersService(): return list(chain((bindACLValidations,), binders()))

bind.bindToEntities('acl.impl.**.*Alchemy', binders=binders)
support.createEntitySetup('acl.impl.**.*')
support.listenToEntities(SERVICES, listeners=addService(bindersService))
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

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
    
    print('ACL/Access/*')
    print('ADDED:', groupService.addGroup(1285521629, 'Anonymous'))
    print('FILTER:', groupService.addFilter(1285521629, 'Anonymous', 'Filter1'))
    
    print('ACL/Access')
    print('ADDED:', groupService.addGroup(3232022005, 'Anonymous'))
    print('FILTER:', groupService.addFilter(3232022005, 'Anonymous', 'Filter1'))
    
    print('ACL/Access/*/Group/*/Entry/*/Filter/*')
    print('ADDED:', groupService.addGroup(512347881, 'Anonymous'))
    print('FILTER:', groupService.addFilter(512347881, 'Anonymous', 'Filter1'))
    
    print('Gateway/Custom/*')
    print('ADDED:', groupService.addGroup(903992123, 'Anonymous'))
    print('FILTER:', groupService.addFilter(903992123, 'Anonymous', 'Filter1'))
