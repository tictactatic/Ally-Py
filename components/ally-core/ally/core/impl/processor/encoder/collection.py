'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the collection encoder.
'''

from .base import RequestEncoder, DefineEncoder, encoderSpecifiers, encoderCourrupt
from ally.api.operator.type import TypeModel, TypeProperty
from ally.api.type import Iter
from ally.container.ioc import injected
from ally.core.impl.encdec import EncoderWithSpecifiers
from ally.core.spec.transform.encdec import IEncoder, IRender
from ally.design.processor.assembly import Assembly
from ally.design.processor.branch import Branch
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from collections import Iterable
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)
    
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
        super().__init__(Branch(self.itemEncodeAssembly).included().using(create=RequestEncoder))
        
    def process(self, chain, processing, create:DefineEncoder, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the collection encoder.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(create, DefineEncoder), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, Iter): return
        # The type is not for a collection, nothing to do, just move along
        
        assert isinstance(create.objType, Iter)
        itemType = create.objType.itemType
        
        if DefineEncoder.name in create and create.name: name = create.name
        else:
            if not isinstance(itemType, (TypeModel, TypeProperty)):
                log.error('Cannot get the collection name for item %s', itemType)
                return encoderCourrupt(chain)
            if isinstance(itemType, TypeProperty):
                assert isinstance(itemType, TypeProperty)
                model = itemType.parent
            else: model = itemType
            assert isinstance(model, TypeModel), 'Invalid model %s' % model
            name = self.nameMarkedList % model.name
        
        arg = processing.executeWithAll(create=processing.ctx.create(objType=itemType), **keyargs)
        assert isinstance(arg.create, RequestEncoder), 'Invalid create item %s' % arg.create
        if arg.create.encoder is None:
            log.error('Cannot encode collection item %s', itemType)
            return encoderCourrupt(chain)
        create.encoder = EncoderCollection(name, arg.create.encoder, encoderSpecifiers(create))

# --------------------------------------------------------------------

class EncoderCollection(EncoderWithSpecifiers):
    '''
    Implementation for a @see: IEncoder for collections.
    '''
    
    def __init__(self, name, encoder, specifiers=None):
        '''
        Construct the collection encoder.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(encoder, IEncoder), 'Invalid item encoder %s' % encoder
        super().__init__(specifiers)
        
        self.name = name
        self.encoder = encoder
        
    def encode(self, obj, target, support):
        '''
        @see: IEncoder.encode
        '''
        assert isinstance(obj, Iterable), 'Invalid collection object %s' % obj
        assert isinstance(target, IRender), 'Invalid target %s' % target
        
        target.beginCollection(self.name, **self.populate(obj, support))
        for objItem in obj: self.encoder.encode(objItem, target, support)
        target.end()
        
