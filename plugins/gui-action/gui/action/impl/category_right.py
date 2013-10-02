'''
Created on Sep 4, 2013

@package: gui action
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for actions organized by right
'''

from ..api.category_right import IActionRightService
from ..core.impl.category import ActionCategoryServiceAlchemy
from ..meta.category_right import RightAction
from ally.container.support import setup
from security.meta.right import RightMapped

# --------------------------------------------------------------------

@setup(IActionRightService, name='actionRight')
class ActionRightServiceAlchemy(ActionCategoryServiceAlchemy, IActionRightService):
    '''
    Implementation for @see: IActionRightService.
    '''
    
    def __init__(self):
        ActionCategoryServiceAlchemy.__init__(self, RightMapped, RightAction)