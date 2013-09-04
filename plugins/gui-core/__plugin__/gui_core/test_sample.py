'''
Created on Aug 30, 2013

@author: chupy
'''

from ally.container import app
from ally.container.support import entityFor
import logging
from acl.api.group import IGroupService, Group
from gui.action.api.category_group import IActionGroupService
    
# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# TODO: GAbriel: remove sample data
@app.populate(app.DEVEL)
def populateGroupSamples():
    groupService = entityFor(IGroupService)
    assert isinstance(groupService, IGroupService)
    actionGroup = entityFor(IActionGroupService)
    assert isinstance(actionGroup, IActionGroupService)
    
    groupService.delete('Anonymous')
    try: groupService.getById('Anonymous')
    except:
        group = Group()
        group.Name = 'Anonymous'
        group.IsAnonymous = True
        groupService.insert(group)
    
    actionGroup.addAction('Anonymous', 'menu.request')
