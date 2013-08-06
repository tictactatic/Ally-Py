'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths for properties of model.
'''

from ally.api.operator.type import TypeModel, TypePropertyContainer
from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.http.impl.index import NAME_BLOCK_REST, ACTION_REFERENCE
from ally.core.impl.processor.encoder.base import ExportingSupport
from ally.core.spec.transform import ISpecifier, ITransfrom
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_spec import IDo

# --------------------------------------------------------------------
    
class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    parent = requires(Context)
    invokersGet = requires(dict)

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Context)
    doEncodePath = requires(IDo)
    
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
    encoder = optional(ITransfrom)
    # ---------------------------------------------------------------- Required
    objType = requires(Type)

class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    nodeValues = defines(dict, doc='''
    @rtype: dictionary{Context: object}
    The values used in constructing the paths indexed by corresponding node.
    ''')
       
# --------------------------------------------------------------------

propertyOfModelPathAttributeEncodeExport = ExportingSupport(Support)
# The property of model support export.

@injected
class PropertyOfModelPathAttributeEncode(HandlerProcessor):
    '''
    Implementation for a handler that provides the path encoding in attributes.
    '''
    
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(Invoker=Invoker)
        
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
        create.specifiers.append(AttributesPath(self.nameRef, invoker))

# --------------------------------------------------------------------

class AttributesPath(ISpecifier):
    '''
    Implementation for a @see: ISpecifier for attributes paths.
    '''
    
    def __init__(self, nameRef, invoker):
        '''
        Construct the paths attributes.
        '''
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(invoker.node, Node), 'Invalid invoker node %s' % invoker.node
        assert isinstance(invoker.doEncodePath, IDo), 'Invalid path encode %s' % invoker.doEncodePath
        
        self.nameRef = nameRef
        self.invoker = invoker
        
    def populate(self, obj, specifications, support):
        '''
        @see: ISpecifier.populate
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        if support.nodeValues is None: support.nodeValues = {}
        support.nodeValues[self.invoker.node.parent] = obj
        
        attributes = specifications.get('attributes')
        if attributes is None: attributes = specifications['attributes'] = {}
        assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
        attributes[self.nameRef] = self.invoker.doEncodePath(support)
        
        specifications['indexBlock'] = NAME_BLOCK_REST
        indexAttributesCapture = specifications.get('indexAttributesCapture')
        if indexAttributesCapture is None: indexAttributesCapture = specifications['indexAttributesCapture'] = {}
        assert isinstance(indexAttributesCapture, dict), 'Invalid index attributes capture %s' % indexAttributesCapture
        indexAttributesCapture[self.nameRef] = ACTION_REFERENCE
