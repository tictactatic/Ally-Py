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
from ally.exception import InputError, Ref
from security.api.right import Right
from security.meta.right_type import RightTypeMapped
from sql_alchemy.impl.entity import EntityGetServiceAlchemy, \
    EntityCRUDServiceAlchemy, EntitySupportAlchemy
from sqlalchemy.orm.exc import NoResultFound
from ally.internationalization import _
from ally.api.option import SliceAndTotal

# --------------------------------------------------------------------

@injected
@setup(IRightService, name='rightService')
class RightServiceAlchemy(EntityGetServiceAlchemy, EntityCRUDServiceAlchemy, IRightService):
    '''
    Implementation for @see: IRightService
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, RightMapped, QRight)
        
    def getByName(self, nameType, name):
        '''
        @see: IRightService.getByName
        '''
        assert isinstance(nameType, str), 'Invalid type name %s' % nameType
        assert isinstance(name, str), 'Invalid name %s' % name

        sql = self.session().query(RightMapped).join(RightTypeMapped)
        sql = sql.filter(RightTypeMapped.Name == nameType).filter(RightMapped.Name == name)

        try: return sql.one()
        except NoResultFound: raise InputError(Ref(_('Invalid names for right'), ref=Right.Name))
        
    def getAll(self, typeId=None, q=None, **options):
        '''
        @see: IRightService.getAll
        '''
        # TODO: Gabriel: do proper implementation also check buildQuery for sql is not working properly
        opt = SliceAndTotal(**options)
        if typeId: filter = RightMapped.Type == typeId
        else: filter = None
        if opt.withTotal:
            entities, total = self._getAllWithCount(filter, q, opt.offset, opt.limit)
            return IterPart(entities, total, opt.offset, opt.limit)
        return self._getAll(filter, q, opt.offset, opt.limit)
