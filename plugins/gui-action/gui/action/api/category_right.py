'''
Created on Sep 4, 2013

@package: gui action
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Specifications for actions organized based security right.
'''

from gui.action.api.category import IActionCategoryPrototype
from ally.api.config import service
from security.api.right import Right

# --------------------------------------------------------------------

@service(('CATEGORY', Right))
class IActionRightService(IActionCategoryPrototype):
    '''
    Service that associates actions with security right.
    '''
