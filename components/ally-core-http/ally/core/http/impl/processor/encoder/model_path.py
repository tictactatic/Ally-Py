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
from ally.core.http.spec.transform.index import ACTION_REFERENCE, \
    NAME_BLOCK_REST
from ally.core.spec.resources import Path, Normalizer
from ally.core.spec.transform.encoder import ISpecifier, IEncoder
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.server import IEncoderPath

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
    pathModel = requires(Path)
    
# --------------------------------------------------------------------

@injected
class ModelPathAttributeEncode(HandlerProcessor):
    '''
    Implementation for a handler that provides the path encoding in attributes.
    '''
    
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(support=Support)
        
        self._path = AttributeModelPath(self.nameRef)
        
    def process(self, chain, create:Create, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the path attributes.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if Create.encoder in create and create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, (TypeModel, TypeModelProperty)): return
        # Model not valid for paths, move along.
        
        if create.specifiers is None: create.specifiers = []
        create.specifiers.append(self._path)

# --------------------------------------------------------------------

class AttributeModelPath(ISpecifier):
    '''
    Implementation for a @see: ISpecifier for paths.
    '''
    
    def __init__(self, nameRef):
        '''
        Construct the paths attributes.
        '''
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        
        self.nameRef = nameRef
        
    def populate(self, obj, specifications, support):
        '''
        @see: IAttributes.populate
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        if not support.pathModel: return  # No path to construct attributes for.
        
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert isinstance(support.pathModel, Path), 'Invalid path %s' % support.pathModel
        assert Support.encoderPath in support, 'No path encoder available in %s' % support
        assert isinstance(support.encoderPath, IEncoderPath), 'Invalid path encoder %s' % support.encoderPath
        
        if not support.pathModel.isValid(): return
        assert isinstance(specifications, dict), 'Invalid specifications %s' % specifications
        
        attributes = specifications.get('attributes')
        if attributes is None: attributes = specifications['attributes'] = {}
        assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
        nameRef = support.normalizer.normalize(self.nameRef)
        attributes[nameRef] = support.encoderPath.encode(support.pathModel)
        
        specifications['indexBlock'] = NAME_BLOCK_REST
        indexAttributesCapture = specifications.get('indexAttributesCapture')
        if indexAttributesCapture is None: indexAttributesCapture = specifications['indexAttributesCapture'] = {}
        assert isinstance(indexAttributesCapture, dict), 'Invalid index attributes capture %s' % indexAttributesCapture
        indexAttributesCapture[nameRef] = ACTION_REFERENCE
