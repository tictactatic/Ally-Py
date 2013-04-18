'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths for properties of model.
'''

from ally.api.operator.type import TypeModel, TypeModelProperty
from ally.container.ioc import injected
from ally.core.spec.resources import Path, Normalizer
from ally.core.spec.transform.encoder import ISpecifier, IEncoder
from ally.design.cache import CacheWeak
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IEncoderPath
from ally.core.http.spec.transform.index import NAME_URL, ATTR_ERROR_STATUS, \
    ATTR_ERROR_MESSAGE

# --------------------------------------------------------------------
    
class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    specifiers = defines(list, doc='''
    @rtype: list[ISpecifier]
    The specifiers for attributes with the paths.
    ''')
    # ---------------------------------------------------------------- Optional
    encoder = optional(IEncoder)
    # ---------------------------------------------------------------- Required
    objType = requires(object)
    
class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Optional
    encoderPath = optional(IEncoderPath)
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
    pathsProperties = requires(dict)
    
# --------------------------------------------------------------------

@injected
class PropertyOfModelPathAttributeEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the path encoding in attributes.
    '''
    
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(support=Support)
        
        self._cache = CacheWeak()
        
    def process(self, create:Create, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Create the path attributes.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if Create.encoder in create and create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypeModelProperty) or not isinstance(create.objType.type, TypeModel): return
        # The type is not for a model property, nothing to do, just move along
            
        modelType = create.objType.type
        assert isinstance(modelType, TypeModel)
        assert modelType.hasId(), 'Model type %s, has no id' % modelType
        
        cache = self._cache.key(modelType)
        if not cache.has: cache.value = AttributesPath(self.nameRef, modelType.propertyTypeId())
        
        if create.specifiers is None: create.specifiers = []
        create.specifiers.append(cache.value)

# --------------------------------------------------------------------

class AttributesPath(ISpecifier):
    '''
    Implementation for a @see: ISpecifier for attributes paths.
    '''
    
    def __init__(self, nameRef, propertyType):
        '''
        Construct the paths attributes.
        '''
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        assert isinstance(propertyType, TypeModelProperty), 'Invalid property type %s' % propertyType
        
        self.nameRef = nameRef
        self.propertyType = propertyType
        
    def populate(self, obj, specifications, support, index=None):
        '''
        @see: ISpecifier.populate
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        if not support.pathsProperties: return  # No paths for models.
        
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert isinstance(support.pathsProperties, dict), 'Invalid properties paths %s' % support.pathsProperties
        assert Support.encoderPath in support, 'No path encoder available in %s' % support
        assert isinstance(support.encoderPath, IEncoderPath), 'Invalid path encoder %s' % support.encoderPath
        
        path = support.pathsProperties.get(self.propertyType)
        if not path: return  # No path to construct attributes for.
        assert isinstance(path, Path), 'Invalid path %s' % path
        path.update(obj, self.propertyType)
        if not path.isValid(): return
        
        attributes = specifications.get('attributes')
        if attributes is None: attributes = specifications['attributes'] = {}
        assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
        nameRef = support.normalizer.normalize(self.nameRef)
        attributes[nameRef] = support.encoderPath.encode(path)
        
        specifications['indexPrepare'] = True
        indexAttributesCapture = specifications.get('indexAttributesCapture')
        if indexAttributesCapture is None: indexAttributesCapture = specifications['indexAttributesCapture'] = {}
        assert isinstance(indexAttributesCapture, dict), 'Invalid index attributes capture %s' % indexAttributesCapture
        indexAttributesCapture[nameRef] = NAME_URL
        
        indexAttributesInject = specifications.get('indexAttributesInject')
        if indexAttributesInject is None: indexAttributesInject = specifications['indexAttributesInject'] = []
        elif isinstance(indexAttributesInject, tuple): indexAttributesInject = list(indexAttributesInject)
        assert isinstance(indexAttributesInject, list), 'Invalid index attributes inject %s' % indexAttributesInject
        indexAttributesInject.append(ATTR_ERROR_STATUS)
        indexAttributesInject.append(ATTR_ERROR_MESSAGE)
