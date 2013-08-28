'''
Created on May 26, 2011

@package: ally api
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

General specifications for the entities API that poses an integer Id identifier.
'''

from ally.api.config import model, query, service
from .entity import IEntityGetPrototype, IEntityFindPrototype, \
    IEntityQueryPrototype

# --------------------------------------------------------------------

@model(id='Id')
class Entity:
    '''
    Provides the basic container for an entity that has a Id identifier.
    '''
    Id = int

# --------------------------------------------------------------------

@query(Entity)
class QEntity:
    '''
    Provides the basic query for an entity.
    '''

# --------------------------------------------------------------------

@service(('Entity', Entity))
class IEntityGetService(IEntityGetPrototype):
    '''
    Entity Id identifier service for @see: IEntityGetPrototype
    '''

@service(('Entity', Entity))
class IEntityFindService(IEntityFindPrototype):
    '''
    Entity Id identifier service for @see: IEntityFindService
    '''

@service(('Entity', Entity), ('QEntity', QEntity))
class IEntityQueryService(IEntityQueryPrototype):
    '''
    Entity Id identifier service for @see: IEntityQueryService
    '''

@service(('Entity', Entity))
class IEntityCRUDService:
    '''
    Entity Id identifier service for @see: IEntityCRUDService
    '''
    
@service
class IEntityGetCRUDService(IEntityGetService, IEntityCRUDService):
    '''
    Provides the get and CRUD.
    '''

@service
class IEntityNQService(IEntityGetService, IEntityFindService, IEntityCRUDService):
    '''
    Provides the find without querying, CRUD and query entity services.
    '''

@service
class IEntityService(IEntityGetService, IEntityQueryService, IEntityCRUDService):
    '''
    Provides the find, CRUD and query entity services.
    '''
