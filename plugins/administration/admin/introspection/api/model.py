'''
Created on Jan 23, 2012

@package: administration
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Nistor Gabriel

API specifications for the REST application model introspection.
'''

from admin.api.domain_admin import modelAdmin
from ally.api.config import service, call, query
from ally.api.criteria import AsLikeOrdered, AsBooleanOrdered
from ally.api.option import SliceAndTotal # @UnusedImport
from ally.api.type import Iter

# --------------------------------------------------------------------

@modelAdmin(id='API')
class Model:
    '''
    The REST model definition.
    '''
    API = str
    Name = str
    Description = str
    
@modelAdmin(id='API')
class Property:
    '''
    The REST model property definition.
    '''
    API = str
    Parent = Model
    IsId = bool
    Name = str
    Type = str
    Refer = Model

# --------------------------------------------------------------------

@query(Model)
class QModel:
    '''
    Provides the model query.
    '''
    api = AsLikeOrdered
    isId = AsBooleanOrdered
    name = AsLikeOrdered

# --------------------------------------------------------------------

@service
class IModelService:
    '''
    Provides services for the REST model resources introspection available for the application.
    '''
    
    @call
    def getModel(self, api:Model.API) -> Model:
        '''
        Provides the model for the provided id.
        '''
        
    @call
    def getProperty(self, api:Property.API) -> Property:
        '''
        Provides the property for the provided id.
        '''
        
    @call
    def getModels(self, q:QModel=None, **options:SliceAndTotal) -> Iter(Model.API):
        '''
        Provides all the models with optional query filtering.
        '''
    
    @call
    def getProperties(self, **options:SliceAndTotal) -> Iter(Property.API):
        '''
        Provides all the properties.
        '''
        
    @call(webName='Related')
    def getModelRelations(self, api:Model.API) -> Iter(Model.API):
        '''
        Provides the models that the provided model is in relation with.
        '''
        
    @call
    def getModelProperties(self, modelAPI:Model.API) -> Iter(Property.API):
        '''
        Provides the properties of the provided model id.
        '''
