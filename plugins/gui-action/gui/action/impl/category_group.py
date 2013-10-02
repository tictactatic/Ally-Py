'''
Created on Sep 4, 2013

@package: gui action
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Balaceanu

Implementation for actions organized by group
'''

from ..api.category_group import IActionGroupService
from ..core.impl.category import ActionCategoryServiceAlchemy
from ..meta.category_group import GroupAction
from acl.meta.group import GroupMapped
from ally.container.support import setup

# --------------------------------------------------------------------

@setup(IActionGroupService, name='actionGroup')
class ActionGroupServiceAlchemy(ActionCategoryServiceAlchemy, IActionGroupService):
    '''
    Implementation for @see: IActionGroupService.
    '''
    
    def __init__(self):
        ActionCategoryServiceAlchemy.__init__(self, GroupMapped, GroupAction)