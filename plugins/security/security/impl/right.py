'''
Created on Mar 6, 2012

@package: superdesk person
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for right type.
'''

from ..api.right import IRightService, QRight
from ..meta.right import RightMapped
from ally.api.extension import IterPart
from ally.container.ioc import injected
from ally.container.support import setup
from sql_alchemy.impl.entity import EntityGetServiceAlchemy, \
    EntityCRUDServiceAlchemy, EntitySupportAlchemy

# --------------------------------------------------------------------

@injected
@setup(IRightService, name='rightService')
class RightServiceAlchemy(EntityGetServiceAlchemy, EntityCRUDServiceAlchemy, IRightService):
    '''
    Implementation for @see: IRightService
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, RightMapped, QRight)
        
    def getAll(self, typeId=None, offset=None, limit=None, detailed=False, q=None):
        '''
        @see: IRightService.getAll
        '''
        if typeId: filter = RightMapped.Type == typeId
        else: filter = None
        if detailed:
            entities, total = self._getAllWithCount(filter, q, offset, limit)
            return IterPart(entities, total, offset, limit)
        return self._getAll(filter, q, offset, limit)
