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
    
    print('ADDED:', groupService.addGroup(1285521629, 'Anonymous'), 'GET:ACL/Access/*')
    print('FILTER:', groupService.addFilter(1285521629, 'Anonymous', 'Filter1'), 'GET:ACL/Access/*')
