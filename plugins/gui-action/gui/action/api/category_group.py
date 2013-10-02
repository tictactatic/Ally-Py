'''
Created on Sep 4, 2013

@package: gui action
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Specifications for actions organized based ACL group.
'''

from gui.action.api.category import IActionCategoryPrototype
from ally.api.config import service
from acl.api.group import Group

# --------------------------------------------------------------------

@service(('CATEGORY', Group))
class IActionGroupService(IActionCategoryPrototype):
    '''
    Service that associates actions with ACL group.
    '''
