'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the paths for a model.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.http.impl.index import ACTION_REFERENCE, NAME_BLOCK_REST
from ally.core.spec.transform import ISpecifier, ITransfrom
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_spec import IDo

# --------------------------------------------------------------------
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    invokerGet = requires(Context)
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
        super().__init__()
        
    def process(self, chain, invoker:Invoker, create:Create, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the path attributes.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if not invoker.invokerGet: return  # No get model invokers available
        assert isinstance(invoker.invokerGet, Invoker), 'Invalid invoker %s' % invoker.invokerGet
        if Create.encoder in create and create.encoder is not None: return 
        # There is already an encoder, nothing to do.
       
        if create.specifiers is None: create.specifiers = []
        create.specifiers.append(AttributeModelPath(self.nameRef, invoker.invokerGet))

# --------------------------------------------------------------------

class AttributeModelPath(ISpecifier):
    '''
    Implementation for a @see: ISpecifier for paths.
    '''
    
    def __init__(self, nameRef, invoker):
        '''
        Construct the paths attributes.
        '''
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(invoker.doEncodePath, IDo), 'Invalid path encode %s' % invoker.doEncodePath
        
        self.nameRef = nameRef
        self.invoker = invoker
        
    def populate(self, obj, specifications, support):
        '''
        @see: IAttributes.populate
        '''
        assert isinstance(specifications, dict), 'Invalid specifications %s' % specifications
        
        attributes = specifications.get('attributes')
        if attributes is None: attributes = specifications['attributes'] = {}
        assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
        attributes[self.nameRef] = self.invoker.doEncodePath(support)
        
        specifications['indexBlock'] = NAME_BLOCK_REST
        indexAttributesCapture = specifications.get('indexAttributesCapture')
        if indexAttributesCapture is None: indexAttributesCapture = specifications['indexAttributesCapture'] = {}
        assert isinstance(indexAttributesCapture, dict), 'Invalid index attributes capture %s' % indexAttributesCapture
        indexAttributesCapture[self.nameRef] = ACTION_REFERENCE
