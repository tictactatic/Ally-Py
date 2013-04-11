'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the collection encoder.
'''

from ally.api.operator.container import Model
from ally.api.operator.type import TypeModel, TypeModelProperty
from ally.api.type import Iter
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer
from ally.core.spec.transform.encoder import IAttributes, IEncoder, \
    EncoderWithAttributes
from ally.core.spec.transform.render import IRender
from ally.design.cache import CacheWeak
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.branch import Included
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranchingProceed
from ally.exception import DevelError
from collections import Iterable

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder for the collection.
    ''')
    # ---------------------------------------------------------------- Optional
    name = optional(str)
    attributes = optional(IAttributes)
    # ---------------------------------------------------------------- Required
    objType = requires(object)

class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
  
class CreateItem(Context):
    '''
    The create item encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    objType = defines(object, doc='''
    @rtype: object
    The type of the collection items.
    ''')
    # ---------------------------------------------------------------- Required
    encoder = requires(IEncoder)
    
# --------------------------------------------------------------------

@injected
class CollectionEncode(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the collection encoding.
    '''
    
    itemEncodeAssembly = Assembly
    # The encode processors to be used for encoding items
    nameMarkedList = '%sList'
    # The name to use for rendering lists of models, contains the '%s' mark where to place the item name.
    
    def __init__(self):
        assert isinstance(self.itemEncodeAssembly, Assembly), 'Invalid item encode assembly %s' % self.itemEncodeAssembly
        assert isinstance(self.nameMarkedList, str), 'Invalid name list %s' % self.nameMarkedList
        super().__init__(Included(self.itemEncodeAssembly).using(create=CreateItem), support=Support)
        
        self._cache = CacheWeak()
        
    def process(self, itemProcessing, create:Create, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Create the collection encoder.
        '''
        assert isinstance(itemProcessing, Processing), 'Invalid processing %s' % itemProcessing
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, Iter): return
        # The type is not for a collection, nothing to do, just move along
        
        assert isinstance(create.objType, Iter)
        itemType = create.objType.itemType
        
        if Create.name in create and create.name: name = create.name
        else:
            if not isinstance(itemType, (TypeModel, TypeModelProperty)):
                raise DevelError('Cannot get collection name for item %s' % itemType)
            assert isinstance(itemType.container, Model), 'Invalid model %s' % itemType.container
            name = self.nameMarkedList % itemType.container.name
        if Create.attributes in create: attributes = create.attributes
        else: attributes = None
        
        cache = self._cache.key(itemProcessing, name, attributes, itemType)
        if not cache.has:
            chain = Chain(itemProcessing)
            chain.process(create=itemProcessing.ctx.create(objType=itemType)).doAll()
            createItem = chain.arg.create
            assert isinstance(createItem, CreateItem), 'Invalid create item %s' % createItem
            if createItem.encoder is None: raise DevelError('Cannot encode %s' % itemType)
            cache.value = EncoderCollection(name, createItem.encoder, attributes)
        
        create.encoder = cache.value

# --------------------------------------------------------------------

class EncoderCollection(EncoderWithAttributes):
    '''
    Implementation for a @see: IEncoder for collections.
    '''
    
    def __init__(self, name, encoder, attributes=None):
        '''
        Construct the collection encoder.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(encoder, IEncoder), 'Invalid item encoder %s' % encoder
        super().__init__(attributes)
        
        self.name = name
        self.encoder = encoder
        
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(obj, Iterable), 'Invalid collection object %s' % obj
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        
        render.beginCollection(support.normalizer.normalize(self.name), self.processAttributes(obj, support))
        for objItem in obj: self.encoder.render(objItem, render, support)
        render.end()
        
        
