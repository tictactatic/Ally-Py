'''
Created on Aug 30, 2013

@author: chupy
'''

from ally.container import app
from ally.container.support import entityFor
import logging
from acl.api.group import IGroupService, Group
from acl.api.access import generateId
    
# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# TODO: GAbriel: remove sample data
@app.populate(app.DEVEL)
def populateGroupSamples():
    groupService = entityFor(IGroupService)
    assert isinstance(groupService, IGroupService)
    
    groupService.delete('Anonymous')
    try: groupService.getById('Anonymous')
    except:
        group = Group()
        group.Name = 'Anonymous'
        group.IsAnonymous = True
        groupService.insert(group)
    
    
#    groupService.addAcl('Anonymous', generateId('User/@/SubUser/*'.replace('@', '*'), 'GET'))
#    ('Anonymous', 'User/@/SubUser/*', 'GET'): [valid:]set('anonymous', 'asas')
#    
#    groupService.remAcl(identifier, accessId)
#    groupService.registerFilter('Anonymous', generateId('User/@/SubUser/*'.replace('@', '*'), 'GET'),
#                                'anonymous', place='User/@/SubUser/*')
    