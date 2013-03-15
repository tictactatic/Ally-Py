'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths for a model.
'''

from ally.api.operator.type import TypeModel, TypeModelProperty
from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.spec.resources import Path, Normalizer
from ally.core.spec.transform.encoder import IAttributes, AttributesJoiner
from ally.design.cache import CacheWeak
from ally.design.processor.attribute import requires, defines
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
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
    pathMain = requires(Path)
    encoderPath = requires(IEncoderPath)
    
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
        
    def process(self, create:Create, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Create the path attributes.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if not isinstance(create.objType, (TypeModel, TypeModelProperty)): return
        # Model not valid for paths, move along.
        
        if create.attributes: attributes = create.attributes
        else: attributes = None
        
        cache = self._cache.key(create.objType, attributes)
        if not cache.has: cache.value = AttributesPath(self.nameRef, create.objType, attributes)
        create.attributes = cache.value

# --------------------------------------------------------------------

class AttributesPath(AttributesJoiner):
    '''
    Implementation for a @see: IAttributes for paths.
    '''
    
    def __init__(self, nameRef, objType, attributes=None):
        '''
        Construct the paths attributes.
        '''
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        assert isinstance(objType, Type), 'Invalid object type %s' % objType
        super().__init__(attributes)
        
        self.nameRef = nameRef
        self.objType = objType
        
    def provideIntern(self, obj, support):
        '''
        @see: AttributesJoiner.provideIntern
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        if not support.pathMain: return  # No path to construct attributes for.
        
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert isinstance(support.pathMain, Path), 'Invalid path %s' % support.pathMain
        assert isinstance(support.encoderPath, IEncoderPath), 'Invalid path encoder %s' % support.encoderPath
        
        support.pathMain.update(obj, self.objType)
        return {support.normalizer.normalize(self.nameRef): support.encoderPath.encode(support.pathMain)}
