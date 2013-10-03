'''
Created on Jan 23, 2012

@package: administration
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Nistor Gabriel

The implementation for the model introspection.
'''

from ..api.model import IModelService, Model, QModel
from ally.api.error import IdError
from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.support.api.util_service import processCollection
from collections import OrderedDict

# --------------------------------------------------------------------

class Introspect(Context):
    '''
    The introspection context.
    '''
    # ---------------------------------------------------------------- Required
    models = requires(OrderedDict)
    modelsRelations = requires(dict)
    properties = requires(OrderedDict)
    modelsProperties = requires(dict)

# --------------------------------------------------------------------

@injected
class ModelService(IModelService):
    '''
    Provides the implementation for @see: IModelService.
    '''
    
    CONTEXTS = dict(introspect=Introspect)
    # The introspect contexts.
    processing = Processing
    # The introspect processing used for obtaining the introspection data.

    def __init__(self):
        '''
        Constructs the request introspect service.
        '''
        assert isinstance(self.processing, Processing), 'Invalid introspect processing %s' % self.processing
        
    def getModel(self, api):
        '''
        @see: IIntrospectService.getModel
        '''
        intr = self.processing.execute(Introspect=self.processing.ctx.introspect).introspect
        assert isinstance(intr, Introspect), 'Invalid introspect %s' % intr
        
        model = intr.models.get(api)
        if model is None: raise IdError()
        return model
    
    def getProperty(self, api):
        '''
        @see: IModelService.getProperty
        '''
        intr = self.processing.execute(Introspect=self.processing.ctx.introspect).introspect
        assert isinstance(intr, Introspect), 'Invalid introspect %s' % intr
        
        prop = intr.properties.get(api)
        if prop is None: raise IdError()
        return prop
        
    def getModels(self, q=None, **options):
        '''
        @see: IIntrospectService.getModels
        '''
        assert q is None or isinstance(q, QModel), 'Invalid query %s' % q
        
        intr = self.processing.execute(Introspect=self.processing.ctx.introspect).introspect
        assert isinstance(intr, Introspect), 'Invalid introspect %s' % intr
        
        return processCollection(intr.models.keys(), Model, q, lambda api: intr.models[api], **options)
    
    def getModelRelations(self, api):
        '''
        @see: IIntrospectService.getModelRelations
        '''
        intr = self.processing.execute(Introspect=self.processing.ctx.introspect).introspect
        assert isinstance(intr, Introspect), 'Invalid introspect %s' % intr
        
        return intr.modelsRelations.get(api, ())
    
    def getProperties(self, **options):
        '''
        @see: IModelService.getProperties
        '''
        intr = self.processing.execute(Introspect=self.processing.ctx.introspect).introspect
        assert isinstance(intr, Introspect), 'Invalid introspect %s' % intr
        
        return processCollection(intr.properties.keys(), **options)
    
    def getModelProperties(self, modelAPI):
        '''
        @see: IModelService.getModelProperties
        '''
        intr = self.processing.execute(Introspect=self.processing.ctx.introspect).introspect
        assert isinstance(intr, Introspect), 'Invalid introspect %s' % intr
        
        return intr.modelsProperties.get(modelAPI, ())
    
