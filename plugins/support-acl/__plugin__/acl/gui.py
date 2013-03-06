'''
Created on Jan 15, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the acl setup.
'''

from . import acl
from acl.right_action import RightAction
from acl.spec import TypeAcl
from ally.container import ioc
from ally.internationalization import NC_
from gui.action.api.action import IActionManagerService

# --------------------------------------------------------------------

def actionRight(name, description) -> RightAction:
    ''' Create an ACL action right '''
    b = RightAction(name, description)
    actionType().add(b)
    return b

# --------------------------------------------------------------------

@ioc.entity
def actionType() -> TypeAcl:
    b = TypeAcl(NC_('security', 'GUI based access control layer'), NC_('security',
    'Right type for the graphical user interface based access control layer right setups')); yield b
    acl.acl().add(b)
    
@ioc.entity
def defaultRight() -> RightAction:
    b = RightAction('default', 'Default GUI right')
    actionType().addDefault(b)
    return b

# --------------------------------------------------------------------

setup = acl.setup

# --------------------------------------------------------------------

@setup
def updateDefault():
    defaultRight().allGet(IActionManagerService)
