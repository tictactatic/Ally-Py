'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths for properties of model.
'''

from ally.api.operator.type import TypeModel, TypeProperty, \
    TypePropertyContainer
from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.http.spec.server import IEncoderPathInvoker
from ally.core.http.spec.transform.index import NAME_BLOCK_REST, \
    ACTION_REFERENCE
from ally.core.spec.transform.encdec import ISpecifier, IEncoder
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------
    
class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokersGet = requires(dict)
    
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
    objType = requires(Type)
    
class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Required
    pathValues = requires(dict)
    encoderPathInvoker = requires(IEncoderPathInvoker)
    
# --------------------------------------------------------------------

@injected
class PropertyOfModelPathAttributeEncode(HandlerProcessor):
    '''
    Implementation for a handler that provides the path encoding in attributes.
    '''
    
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(Support=Support)
        
    def process(self, chain, node:Node, create:Create, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the path attributes.
        '''
        assert isinstance(node, Node), 'Invalid node %s' % node
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if not node.invokersGet: return  # No get invokers available
        assert isinstance(node.invokersGet, dict), 'Invalid get invokers %s' % node.invokersGet
        if Create.encoder in create and create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypePropertyContainer): return
        # The type is not for a model property, nothing to do, just move along
        assert isinstance(create.objType, TypePropertyContainer)
        model = create.objType.container
        if not isinstance(model, TypeModel): return  # The container is not a model, move along.
        assert isinstance(model, TypeModel)
        if not model.propertyId: return  # No model id to use.
        
        invoker = node.invokersGet.get(model.propertyId)
        if invoker is None: return  # No get invoker available
        
        if create.specifiers is None: create.specifiers = []
        create.specifiers.append(AttributesPath(self.nameRef, model.propertyId, invoker))

# --------------------------------------------------------------------

class AttributesPath(ISpecifier):
    '''
    Implementation for a @see: ISpecifier for attributes paths.
    '''
    
    def __init__(self, nameRef, property, invoker):
        '''
        Construct the paths attributes.
        '''
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        assert isinstance(property, TypeProperty), 'Invalid property type %s' % property
        
        self.nameRef = nameRef
        self.property = property
        self.invoker = invoker
        
    def populate(self, obj, specifications, support):
        '''
        @see: ISpecifier.populate
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.encoderPathInvoker, IEncoderPathInvoker), \
        'Invalid encoder path %s' % support.encoderPathInvoker
        
        if support.pathValues is None: support.pathValues = {}
        support.pathValues[self.property] = obj
        
        attributes = specifications.get('attributes')
        if attributes is None: attributes = specifications['attributes'] = {}
        assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
        attributes[self.nameRef] = support.encoderPathInvoker.encode(self.invoker, support.pathValues)
        
        specifications['indexBlock'] = NAME_BLOCK_REST
        indexAttributesCapture = specifications.get('indexAttributesCapture')
        if indexAttributesCapture is None: indexAttributesCapture = specifications['indexAttributesCapture'] = {}
        assert isinstance(indexAttributesCapture, dict), 'Invalid index attributes capture %s' % indexAttributesCapture
        indexAttributesCapture[self.nameRef] = ACTION_REFERENCE
