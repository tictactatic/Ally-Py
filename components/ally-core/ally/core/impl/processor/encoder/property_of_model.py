'''
Created on Mar 11, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the properties of model encoder.
'''

from ally.api.operator.type import TypeModelProperty, TypeModel
from ally.container.ioc import injected
from ally.core.spec.transform.encoder import DO_RENDER
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranching
from ally.design.processor.processor import Included

# --------------------------------------------------------------------

class Response(Context):
    '''
    The encoded response context.
    '''
    # ---------------------------------------------------------------- Required
    action = requires(int)

class Encode(Context):
    '''
    The encode context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    obj = requires(object)
    objType = requires(object)

# --------------------------------------------------------------------

@injected
class PropertyOfModelEncode(HandlerBranching):
    '''
    Implementation for a handler that provides the encoding for properties that reference another model.
    '''
    
    propertyModelEncodeAssembly = Assembly
    # The encode processors to be used for encoding model properties.
    
    def __init__(self):
        assert isinstance(self.propertyModelEncodeAssembly, Assembly), \
        'Invalid model encode assembly %s' % self.propertyModelEncodeAssembly
        super().__init__(Included(self.propertyModelEncodeAssembly))
        
    def process(self, chain, propertyModelProcessing, response:Response, encode:Encode, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Encode the property of model.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(propertyModelProcessing, Processing), 'Invalid processing %s' % propertyModelProcessing
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(encode, Encode), 'Invalid encode %s' % encode
        
        chain.proceed()  # We proceed anyway
        
        if not response.action & DO_RENDER: return
        # If no rendering is required we just proceed, maybe other processors might do something
        if not isinstance(encode.objType, TypeModelProperty) or not isinstance(encode.objType.type, TypeModel): return
        # The type is not for a model property, nothing to do, just move along
            
        modelType = encode.objType.type
        
        assert encode.obj is not None, 'An object is required for rendering'
        assert isinstance(encode.name, str), 'Invalid property name %s' % encode.name
        assert isinstance(modelType, TypeModel)
        assert modelType.hasId(), 'Model type %s, has no id' % modelType

        encode.objType = modelType.propertyTypeId()
        chain.branch(propertyModelProcessing)
