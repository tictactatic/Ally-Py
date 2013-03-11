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
from ally.core.spec.transform.encoder import DO_RENDER
from ally.core.spec.transform.render import IRender
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing, CONSUMED
from ally.design.processor.handler import HandlerBranching
from ally.design.processor.processor import Included
from ally.exception import DevelError
from collections import Iterable

# --------------------------------------------------------------------

class Response(Context):
    '''
    The encoded response context.
    '''
    # ---------------------------------------------------------------- Required
    action = requires(int)
    normalizer = requires(Normalizer)

class EncodeCollection(Context):
    '''
    The encode collection context.
    '''
    # ---------------------------------------------------------------- Optional
    name = optional(str)
    attributes = optional(dict)
    # ---------------------------------------------------------------- Required
    obj = requires(object)
    objType = requires(object)
    render = requires(IRender)
    
class EncodeItem(Context):
    '''
    The encode item context.
    '''
    # ---------------------------------------------------------------- Defined
    obj = defines(object, doc='''
    @rtype: object
    The item object.
    ''')
    objType = defines(object, doc='''
    @rtype: object
    The type of the collection items.
    ''')
    render = defines(IRender, doc='''
    @rtype: IRender
    The renderer to be used for output encoded item data.
    ''')
    
# --------------------------------------------------------------------

@injected
class CollectionEncode(HandlerBranching):
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
        super().__init__(Included(self.itemEncodeAssembly).using(encode=EncodeItem))
        
    def process(self, chain, itemProcessing, response:Response, encode:EncodeCollection, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Encode the collection.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(itemProcessing, Processing), 'Invalid processing %s' % itemProcessing
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(encode, EncodeCollection), 'Invalid encode %s' % encode
        
        if not response.action & DO_RENDER:
            # If no rendering is required we just proceed, maybe other processors might do something
            chain.proceed()
            return
        
        if not isinstance(encode.objType, Iter):  # The type is not for a collection, nothing to do, just move along
            chain.proceed()
            return
        
        assert encode.obj is not None, 'An object is required for rendering'
        assert isinstance(encode.objType, Iter)
        itemType = encode.objType.itemType
        
        assert isinstance(response.normalizer, Normalizer), 'Invalid normalizer %s' % response.normalizer
        assert isinstance(encode.render, IRender), 'Invalid render %s' % encode.render
        
        if EncodeCollection.name in encode and encode.name: name = response.normalizer.normalize(encode.name)
        else:
            if not isinstance(itemType, (TypeModel, TypeModelProperty)):
                raise DevelError('Cannot get collection name for item %s' % itemType)
            assert isinstance(itemType.container, Model), 'Invalid model %s' % itemType.container
            name = response.normalizer.normalize(self.nameMarkedList % itemType.container.name)
        if EncodeCollection.attributes in encode: attributes = encode.attributes
        else: attributes = None
        
        assert isinstance(encode.obj, Iterable), 'Invalid collection object %s' % encode.obj
        encode.render.collectionStart(name, attributes)
        for item in encode.obj:
            encodeItem = itemProcessing.ctx.encode(render=encode.render)
            assert isinstance(encodeItem, EncodeItem), 'Invalid encode item %s' % encodeItem
            encodeItem.objType = itemType
            encodeItem.obj = item
            if Chain(itemProcessing).execute(CONSUMED, response=response, encode=encodeItem, **keyargs):
                raise DevelError('Cannot encode %s' % itemType)
        encode.render.collectionEnd()
