'''
Created on Mar 6, 2012

@package: security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for right.
'''

from ..api.right import IRightService, QRight
from ..meta.right import RightMapped
from ally.container.ioc import injected
from ally.container.support import setup
from ally.support.sqlalchemy.util_service import buildQuery, \
    iterateCollection
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
        
    def getAll(self, typeId=None, q=None, **options):
        '''
        @see: IRightService.getAll
        '''
        sqlQuery = self.session().query(RightMapped.Id)
        if typeId: sqlQuery = sqlQuery.filter(RightMapped.Type == typeId)
        if q is not None:
            assert isinstance(q, QRight), 'Invalid query %s' % q
            sqlQuery = buildQuery(sqlQuery, q, RightMapped)
        return iterateCollection(sqlQuery, **options)
