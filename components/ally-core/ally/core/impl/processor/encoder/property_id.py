'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the id properties encoder.
'''

from ally.api.operator.type import TypeModelProperty
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer, Converter
from ally.core.spec.transform.encoder import DO_RENDER
from ally.core.spec.transform.render import IRender
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Response(Context):
    '''
    The encoded response context.
    '''
    # ---------------------------------------------------------------- Required
    action = requires(int)
    normalizer = requires(Normalizer)
    converterId = requires(Converter)

class Encode(Context):
    '''
    The encode context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    obj = requires(object)
    objType = requires(object)
    render = requires(IRender)
    
# --------------------------------------------------------------------

@injected
class PropertyIdEncode(HandlerProcessor):
    '''
    Implementation for a handler that provides the id properties values encoding.
    '''
        
    def process(self, chain, response:Response, encode:Encode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Encode the id property.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(encode, Encode), 'Invalid encode %s' % encode
        
        if not response.action & DO_RENDER:
            # If no rendering is required we just proceed, maybe other processors might do something
            chain.proceed()
            return
        
        if not isinstance(encode.objType, TypeModelProperty):  # The type is not for a property, nothing to do, just move along
            chain.proceed()
            return
        
        assert isinstance(encode.objType, TypeModelProperty)
        if not encode.objType.isId():  # Not a id property, nothing to do, just move along
            chain.proceed()
            return
        
        assert encode.obj is not None, 'An object is required for rendering'
        assert isinstance(encode.name, str), 'Invalid property name %s' % encode.name
        assert isinstance(encode.render, IRender), 'Invalid render %s' % encode.render
        assert isinstance(response.normalizer, Normalizer), 'Invalid normalizer %s' % response.normalizer
        assert isinstance(response.converterId, Converter), 'Invalid converter %s' % response.converterId

        encode.render.value(response.normalizer.normalize(encode.name),
                            response.converterId.asString(encode.obj, encode.objType.type))
