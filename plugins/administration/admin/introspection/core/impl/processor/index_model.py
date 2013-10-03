'''
Created on Oct 1, 2013

@package: administration
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that indexes the @see: Model objects for the introspect.
'''

from admin.introspection.api.model import Model, Property
from admin.introspection.core.spec import modelId, propertyId
from ally.api.operator.type import TypeModel, TypeProperty, \
    TypePropertyContainer
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from collections import OrderedDict
from pydoc import getdoc

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    relations = requires(dict)
    
class Introspect(Context):
    '''
    The introspect context.
    '''
    # ---------------------------------------------------------------- Defined
    models = defines(OrderedDict, doc='''
    @rtype: dictionary{string: Model}
    The introspect Model objects indexed by the API id. 
    ''')
    modelsRelations = defines(dict, doc='''
    @rtype: dictionary{string: list[string]}
    The dictionary containing the model relations API ids indexed by the relation model API id.
    ''')
    properties = defines(OrderedDict, doc='''
    @rtype: dictionary{string: Property}
    The introspect Property objects indexed by the API id. 
    ''')
    modelsProperties = defines(dict, doc='''
    @rtype: dictionary{string: list[string]}
    The introspect Property objects associated with the indexed model API id. 
    ''')
      
# --------------------------------------------------------------------

class IndexModelHandler(HandlerProcessor):
    '''
    Provides the indexes the @see: Model objects for the introspect.
    '''
    
    hintDomain = 'domain'
    # The hint name for domain.
    
    def __init__(self):
        assert isinstance(self.hintDomain, str), 'Invalid domain hint %s' % self.hintDomain
        super().__init__()
    
    def process(self, chain, register:Register, introspect:Introspect, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Index the introspection request object.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(introspect, Introspect), 'Invalid introspect %s' % introspect
        
        if introspect.models is None: introspect.models = OrderedDict()
        if introspect.properties is None: introspect.properties = OrderedDict()
        if introspect.modelsRelations is None: introspect.modelsRelations = {}
        if introspect.modelsProperties is None: introspect.modelsProperties = {}
        if not register.relations: return  # No models available
        
        models, properties = [], []
        for typeModel, relations in register.relations.items():
            assert isinstance(typeModel, TypeModel), 'Invalid model %s' % typeModel
            assert isinstance(relations, set), 'Invalid relation set %s' % relations
            
            model = Model()
            models.append(model)
            
            domain = typeModel.hints.get(self.hintDomain)
            
            model.API = modelId(typeModel)
            if domain: model.Name = '%s/%s' % (domain.rstrip('/'), typeModel.name)
            else: model.Name = typeModel.name 
            model.Description = getdoc(typeModel.clazz)
            
            ids = introspect.modelsRelations.get(model.API)
            if ids is None: ids = introspect.modelsRelations[model.API] = []
            ids.extend(modelId(rTypeModel) for rTypeModel in relations if rTypeModel != typeModel)
            
            modelsProperties = introspect.modelsProperties.get(model.API)
            if modelsProperties is None: modelsProperties = introspect.modelsProperties[model.API] = []
            for typeProperty in typeModel.properties.values():
                assert isinstance(typeProperty, TypeProperty), 'Invalid property %s' % typeProperty
                
                prop = Property()
                properties.append(prop)
                
                prop.API = propertyId(typeProperty)
                prop.Parent = model.API
                prop.IsId = typeProperty == typeModel.propertyId
                prop.Name = typeProperty.name
                prop.Type = str(typeProperty.type)
                if isinstance(typeProperty, TypePropertyContainer):
                    assert isinstance(typeProperty, TypePropertyContainer)
                    prop.Refer = modelId(typeProperty.container)
                
                modelsProperties.append(prop.API)
        
        models.sort(key=lambda model: model.API)
        introspect.models.update((model.API, model) for model in models)
        
        for relations in introspect.modelsRelations.values():
            relations.sort(key=lambda api: introspect.models[api].API)
        
        properties.sort(key=lambda prop: prop.Name)
        properties.sort(key=lambda prop: introspect.models[prop.Parent].API)
        introspect.properties.update((prop.API, prop) for prop in properties)
        
        for modelsProperties in introspect.modelsProperties.values():
            modelsProperties.sort(key=lambda api: introspect.properties[api].Name)
            modelsProperties.sort(key=lambda api: introspect.properties[api].IsId, reverse=True)
