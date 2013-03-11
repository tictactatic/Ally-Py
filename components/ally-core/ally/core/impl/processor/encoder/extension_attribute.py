'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the extension encoder.
'''

from ally.api.operator.type import TypeExtension
from ally.api.type import typeFor
from ally.container.ioc import injected
from ally.core.spec.transform.encoder import DO_RENDER
from ally.core.spec.transform.render import IRender, RenderValuesToObject
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing, CONSUMED
from ally.design.processor.handler import HandlerBranchingProceed
from ally.design.processor.processor import Included
from ally.exception import DevelError

# --------------------------------------------------------------------

class Response(Context):
    '''
    The encoded response context.
    '''
    # ---------------------------------------------------------------- Required
    action = requires(int)

class EncodeExtension(Context):
    '''
    The encode extension context.
    '''
    # ---------------------------------------------------------------- Optional
    obj = requires(object)
    objType = requires(object)
    # ---------------------------------------------------------------- Defined
    attributes = defines(dict, doc='''
    @rtype: dictionary{string: string}
    The attributes from the extension.
    ''')

class EncodeProperty(Context):
    '''
    The encode property context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The name used to render the property with.
    ''')
    obj = defines(object, doc='''
    @rtype: object
    The property value object.
    ''')
    objType = defines(object, doc='''
    @rtype: object
    The type of the property.
    ''')
    render = defines(IRender, doc='''
    @rtype: IRender
    The renderer to be used for output encoded item data.
    ''')
    
# --------------------------------------------------------------------

@injected
class ExtensionEncode(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the extension encoding in attributes.
    '''
    
    propertyPrimitiveEncodeAssembly = Assembly
    # The encode processors to be used for encoding primitive properties.
    
    def __init__(self):
        assert isinstance(self.propertyPrimitiveEncodeAssembly, Assembly), \
        'Invalid property encode assembly %s' % self.propertyPrimitiveEncodeAssembly
        super().__init__(Included(self.propertyPrimitiveEncodeAssembly).using(encode=EncodeProperty))
        
    def process(self, propertyProcessing, response:Response, encode:EncodeExtension, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Encode the extension.
        '''
        assert isinstance(propertyProcessing, Processing), 'Invalid processing %s' % propertyProcessing
        assert isinstance(response, Response), 'Invalid support %s' % response
        assert isinstance(encode, EncodeExtension), 'Invalid encode %s' % encode
        
        if not response.action & DO_RENDER: return
        # If no rendering is required we just proceed, maybe other processors might do something
        typeExt = typeFor(encode.obj)
        if not typeExt or not isinstance(typeExt, TypeExtension): return
        # Is not an extension object, nothing to do
        assert isinstance(typeExt, TypeExtension)
   
        renderAttributes = RenderValuesToObject()
        for propType in typeExt.propertyTypes():
            value = getattr(encode.obj, propType.property)
            if value is None: continue
            encodeProperty = propertyProcessing.ctx.encode(render=renderAttributes)
            assert isinstance(encodeProperty, EncodeProperty), 'Invalid encode property %s' % encodeProperty
            encodeProperty.objType = propType
            encodeProperty.obj = value
            encodeProperty.name = propType.property
            if Chain(propertyProcessing).execute(CONSUMED, response=response, encode=encodeProperty, **keyargs):
                raise DevelError('Cannot encode %s' % propType)
        
        if encode.attributes is None: encode.attributes = renderAttributes.obj
        else: encode.attributes.update(renderAttributes.obj)
