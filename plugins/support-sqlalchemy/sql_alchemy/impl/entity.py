'''
Created on Jun 23, 2011

@package: support plugin
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

SQL alchemy implementation for the generic ided or named entities API.
'''

from ally.api.error import IdError
from ally.api.operator.type import TypeModel, TypeProperty, TypeQuery
from ally.api.type import typeFor
from ally.support.api.util_service import getModelId
from ally.support.sqlalchemy.mapper import MappedSupport
from ally.support.sqlalchemy.session import SessionSupport
from ally.support.sqlalchemy.util_service import buildQuery, \
    iterateCollection, insertModel, updateModel
from inspect import isclass
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class EntitySupportAlchemy(SessionSupport):
    '''
    Provides support generic entity handling.
    '''

    def __init__(self, Mapped, QEntity=None):
        '''
        Construct the entity support for the provided model class and query class.
        
        @param Mapped: class
            The mapped entity model class.
        @param QEntity: class|None
            The query mapped class if there is one.
        '''
        assert isclass(Mapped), 'Invalid class %s' % Mapped
        assert isinstance(Mapped, MappedSupport), 'Invalid mapped class %s' % Mapped
        model = typeFor(Mapped)
        assert isinstance(model, TypeModel), 'Invalid model class %s' % Mapped
        assert isinstance(model.propertyId, TypeProperty), 'Invalid model property id %s' % model.propertyId
        
        self.Entity = model.clazz
        self.Mapped = Mapped

        if QEntity is not None:
            assert isclass(QEntity), 'Invalid class %s' % QEntity
            assert isinstance(typeFor(QEntity), TypeQuery), 'Invalid query entity class %s' % QEntity
        self.QEntity = QEntity

# --------------------------------------------------------------------

class EntityGetServiceAlchemy(EntitySupportAlchemy):
    '''
    Generic implementation for @see: IEntityGetService
    '''

    def getById(self, id):
        '''
        @see: IEntityGetService.getById
        '''
        entity = self.session().query(self.Mapped).get(id)
        if entity is None: raise IdError(self.Entity)
        return entity

class EntityFindServiceAlchemy(EntitySupportAlchemy):
    '''
    Generic implementation for @see: IEntityFindService
    '''

    def getAll(self, **options):
        '''
        @see: IEntityQueryService.getAll
        '''
        return iterateCollection(self.session().query(getModelId(self.Mapped)), **options)

class EntityQueryServiceAlchemy(EntitySupportAlchemy):
    '''
    Generic implementation for @see: IEntityQueryService
    '''

    def getAll(self, q=None, **options):
        '''
        @see: IEntityQueryService.getAll
        '''
        assert self.QEntity is not None, 'No query available for this service'
        sqlQuery = self.session().query(getModelId(self.Mapped))
        if q is not None:
            assert isinstance(q, self.QEntity), 'Invalid query %s' % q
            sqlQuery = buildQuery(sqlQuery, q, self.Mapped)
        return iterateCollection(sqlQuery, **options)

class EntityCRUDServiceAlchemy(EntitySupportAlchemy):
    '''
    Generic implementation for @see: IEntityCRUDService
    '''

    def insert(self, entity):
        '''
        @see: IEntityCRUDService.insert
        '''
        return getModelId(insertModel(self.Mapped, entity))

    def update(self, entity):
        '''
        @see: IEntityCRUDService.update
        '''
        updateModel(self.Mapped, entity)

    def delete(self, id):
        '''
        @see: IEntityCRUDService.delete
        '''
        return self.session().query(self.Entity).filter(self.Entity.Id == id).delete() > 0

class EntityGetCRUDServiceAlchemy(EntityGetServiceAlchemy, EntityCRUDServiceAlchemy):
    '''
    Generic implementation for @see: IEntityGetCRUDService
    '''

class EntityNQServiceAlchemy(EntityGetServiceAlchemy, EntityFindServiceAlchemy, EntityCRUDServiceAlchemy):
    '''
    Generic implementation for @see: IEntityService
    '''

    def __init__(self, Entity):
        '''
        @see: EntitySupportAlchemy.__init__
        '''
        EntitySupportAlchemy.__init__(self, Entity)

class EntityServiceAlchemy(EntityGetServiceAlchemy, EntityQueryServiceAlchemy, EntityCRUDServiceAlchemy):
    '''
    Generic implementation for @see: IEntityService
    '''

