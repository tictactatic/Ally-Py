'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the property encoder.
'''

from ally.api.operator.type import TypeModelProperty
from ally.api.type import Iter
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer, Converter
from ally.core.spec.transform.encoder import DO_RENDER
from ally.core.spec.transform.render import IRender
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerProcessor
from collections import Iterable

# --------------------------------------------------------------------

class Support(Context):
    '''
    The encode support context.
    '''
    # ---------------------------------------------------------------- Required
    doAction = requires(int)
    normalizer = requires(Normalizer)
    converter = requires(Converter)
    converterId = requires(Converter)

class EncodeProperty(Context):
    '''
    The encode collection context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    obj = requires(object)
    objType = requires(object)
    render = requires(IRender)
    
# --------------------------------------------------------------------

@injected
class PropertyEncode(HandlerProcessor):
    '''
    Implementation for a handler that provides the property values encoding.
    '''
    
    nameValue = 'Value'
    # The name to use for rendering the values in a collection property.
    
    def __init__(self):
        assert isinstance(self.nameValue, str), 'Invalid name value list %s' % self.nameValue
        super().__init__()
        
    def process(self, chain, support:Support, encode:EncodeProperty, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Encode the property.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(encode, EncodeProperty), 'Invalid encode %s' % encode
        
        if not support.doAction & DO_RENDER:
            # If no rendering is required we just proceed, maybe other processors might do something
            chain.proceed()
            return
        
        if not isinstance(encode.objType, TypeModelProperty):  # The type is not for a property, nothing to do, just move along
            chain.proceed()
            return
        
        assert encode.obj is not None, 'An object is required for rendering'
        assert isinstance(encode.name, str), 'Invalid property name %s' % encode.name
        assert isinstance(encode.objType, TypeModelProperty)
        assert isinstance(encode.render, IRender), 'Invalid render %s' % encode.render
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert isinstance(support.converter, Converter), 'Invalid converter %s' % support.converter
        
        valueType = encode.objType.type
        
        if isinstance(valueType, Iter):
            assert isinstance(valueType, Iter)
            assert isinstance(encode.obj, Iterable), 'Invalid encode object %s' % encode.obj
            valueType = valueType.itemType
            
            encode.render.collectionStart(encode.name)
            nameValue = support.normalizer.normalize(self.nameValue)
            for value in encode.obj: encode.render.value(nameValue, support.converter.asString(value, valueType))
            encode.render.collectionEnd()
        
        else:
            if encode.objType.isId(): converter = support.converterId
            else: converter = support.converter
            encode.render.value(support.normalizer.normalize(encode.name), converter.asString(encode.obj, valueType))
