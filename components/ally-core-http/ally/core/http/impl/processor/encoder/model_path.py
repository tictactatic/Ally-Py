'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths for a model.
'''

from ally.api.operator.type import TypeModel, TypeModelProperty
from ally.container.ioc import injected
from ally.core.http.spec.transform.index import GROUP_VALUE_REFERENCE
from ally.core.spec.resources import Path, Normalizer
from ally.core.spec.transform.encoder import IAttributes, AttributesWrapper
from ally.core.spec.transform.index import AttrValue
from ally.design.cache import CacheWeak
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IEncoderPath

# --------------------------------------------------------------------
    
class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    attributes = defines(IAttributes, doc='''
    @rtype: IAttributes
    The attributes with the paths.
    ''')
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
    pathModel = requires(Path)
    
# --------------------------------------------------------------------

@injected
class ModelPathAttributeEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the path encoding in attributes.
    '''
    
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(support=Support)
        
        self._cache = CacheWeak()
        self._attributes = AttributesModelPath(self.nameRef)
        
    def process(self, create:Create, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Create the path attributes.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if not isinstance(create.objType, (TypeModel, TypeModelProperty)): return
        # Model not valid for paths, move along.
        
        if create.attributes:
            cache = self._cache.key(create.attributes)
            if not cache.has: cache.value = AttributesModelPath(self.nameRef, create.attributes)
            create.attributes = cache.value
        else:
            create.attributes = self._attributes

# --------------------------------------------------------------------

class AttributesModelPath(AttributesWrapper):
    '''
    Implementation for a @see: IAttributes for paths.
    '''
    
    def __init__(self, nameRef, attributes=None):
        '''
        Construct the paths attributes.
        '''
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        super().__init__(attributes)
        
        self.nameRef = nameRef
        
    def populate(self, obj, attributes, support, index=None):
        '''
        @see: IAttributes.populate
        '''
        super().populate(obj, attributes, support, index)
        
        assert isinstance(support, Support), 'Invalid support %s' % support
        if not support.pathModel: return  # No path to construct attributes for.
        
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert isinstance(support.pathModel, Path), 'Invalid path %s' % support.pathModel
        assert Support.encoderPath in support, 'No path encoder available in %s' % support
        assert isinstance(support.encoderPath, IEncoderPath), 'Invalid path encoder %s' % support.encoderPath
        
        if not support.pathModel.isValid(): return
        assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
        
        nameRef = support.normalizer.normalize(self.nameRef)
        attributes[nameRef] = support.encoderPath.encode(support.pathModel)
        if index is not None:
            assert isinstance(index, list), 'Invalid index %s' % index
            index.append(AttrValue(GROUP_VALUE_REFERENCE, nameRef))
