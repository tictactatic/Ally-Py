'''
Created on May 2, 2012

@package: ally api
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

General specifications for the entities API that poses a string Name identifier.
'''

from ally.api.config import model, query, service, call
from ally.api.option import SliceAndTotal # @UnusedImport
from ally.api.type import Iter

# --------------------------------------------------------------------

@model(id='Name')
class Entity:
    '''
    Provides the basic container for an entity that has a Name as the identifier.
    '''
    Name = str

# --------------------------------------------------------------------

@query(Entity)
class QEntity:
    '''
    Provides the basic query for an entity.
    '''

# --------------------------------------------------------------------

# The Entity model will be replaced by the specific model when the API will be inherited.
@service
class IEntityGetService:
    '''
    Provides the basic entity service. This means locate by id.
    '''

    @call
    def getById(self, name:Entity.Name) -> Entity:
        '''
        Provides the entity based on the name.
        
        @param name: string
            The name of the entity to find.
        '''

@service
class IEntityFindService:
    '''
    Provides the basic entity find service.
    '''

    @call
    def getAll(self, **options:SliceAndTotal) -> Iter(Entity.Name):
        '''
        Provides the entities.
        
        @param options: @see: SliceAndTotal
            The options to fetch the entities with.
        '''

@service
class IEntityQueryService:
    '''
    Provides the entity find service based on a query.
    '''

    @call
    def getAll(self, q:QEntity=None, **options:SliceAndTotal) -> Iter(Entity.Name):
        '''
        Provides the entities searched by the provided query.
        
        @param q: QEntity|None
            The query to search by.
        @param options: @see: SliceAndTotal
            The options to fetch the entities with.
        '''

@service
class IEntityCRUDService:
    '''
    Provides the entity the CRUD services.
    '''

    @call
    def insert(self, entity:Entity) -> Entity.Name:
        '''
        Insert the entity.
        
        @param entity: Entity
            The entity to be inserted.
        @return: string
            The name assigned to the entity
        '''

    @call
    def update(self, entity:Entity):
        '''
        Update the entity.
        
        @param entity: Entity
            The entity to be updated.
        '''

    @call
    def delete(self, name:Entity.Name) -> bool:
        '''
        Delete the entity for the provided key.
        
        @param name: string
            The name of the entity to be deleted.
        @return: boolean
            True if the delete is successful, false otherwise.
        '''

@service
class IEntityGetCRUDService(IEntityGetService, IEntityCRUDService):
    '''
    Provides the get and CRUD.
    '''

@service
class IEntityNQService(IEntityGetService, IEntityFindService, IEntityCRUDService):
    '''
    Provides the find without querying and CRUD services.
    '''

@service
class IEntityService(IEntityGetService, IEntityQueryService, IEntityCRUDService):
    '''
    Provides the find, CRUD and query entity services.
    '''
