'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the property of model path.
'''

from ally.api.operator.type import TypeModel, TypeModelProperty
from ally.container.ioc import injected
from ally.core.spec.resources import Path
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IEncoderPath
from ally.support.core.util_resources import findGetModel

# --------------------------------------------------------------------

class Request(Context):
    '''
    The encoded request context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(Path)

class Response(Context):
    '''
    The encoded response context.
    '''
    # ---------------------------------------------------------------- Required
    encoderPath = requires(IEncoderPath)
    
class Encode(Context):
    '''
    The encode context.
    '''
    # ---------------------------------------------------------------- Required
    obj = requires(object)
    objType = requires(object)
    # ---------------------------------------------------------------- Defined
    attributes = defines(dict, doc='''
    @rtype: dictionary{string: string}
    The attributes with the paths.
    ''')
    
# --------------------------------------------------------------------

@injected
class PathEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the path encoding in attributes.
    '''
    
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__()
        
    def process(self, request:Request, response:Response, encode:Encode, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Encode the path attribute.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(encode, Encode), 'Invalid encode %s' % encode
        
        if isinstance(encode.objType, TypeModel): path = findGetModel(request.path, encode.objType)
        elif isinstance(encode.objType, TypeModelProperty): path = findGetModel(request.path, encode.objType.parent)
        else: return  # No path can be extracted
        if path is None: return  # No path available
        
        path.update(encode.obj, encode.objType)
        
        assert isinstance(response.encoderPath, IEncoderPath), 'Invalid path encoder %s' % response.encoderPath
        
        if encode.attributes is None: encode.attributes = {}
        encode.attributes[self.nameRef] = response.encoderPath.encode(path)
