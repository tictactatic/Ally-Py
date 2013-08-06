'''
Created on Mar 6, 2012

@package: security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for right type.
'''

from ..api.right_type import IRightTypeService
from ..meta.right_type import RightTypeMapped
from ally.container.ioc import injected
from ally.container.support import setup
from sql_alchemy.impl.entity import EntityNQServiceAlchemy

# --------------------------------------------------------------------

@injected
@setup(IRightTypeService, name='rightTypeService')
class RightTypeServiceAlchemy(EntityNQServiceAlchemy, IRightTypeService):
    '''
    Implementation for @see: IRightTypeService.
    '''
    
    def __init__(self):
        EntityNQServiceAlchemy.__init__(self, RightTypeMapped)
