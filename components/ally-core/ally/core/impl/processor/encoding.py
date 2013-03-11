'''
Created on Jul 27, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Renders the response encoder.
'''

from ally.container.ioc import injected
from ally.core.spec.resources import Invoker
from ally.core.spec.transform.encoder import DO_RENDER
from ally.core.spec.transform.render import IRender
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain, CONSUMED
from ally.design.processor.handler import HandlerBranchingProceed
from ally.design.processor.processor import Included
from ally.exception import DevelError
from collections import Callable, Iterable
from io import BytesIO
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Invoker)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    renderFactory = requires(Callable)
    obj = requires(object)
    isSuccess = requires(bool)
    # ---------------------------------------------------------------- Defined
    action = defines(int, doc='''
    @rtype: integer
    Flag indicating what the process that should be performed.
    ''')

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defined
    source = defines(Iterable, doc='''
    @rtype: Iterable
    The generator containing the response content.
    ''')
    length = defines(int)

class Encode(Context):
    '''
    The encode context.
    '''
    # ---------------------------------------------------------------- Required
    obj = defines(object, doc='''
    @rtype: object
    The value object to be encoded.
    ''')
    objType = defines(object, doc='''
    @rtype: object
    The object type.
    ''')
    render = defines(IRender, doc='''
    @rtype: IRender
    The renderer to be used for output encoded data.
    ''')
    
# --------------------------------------------------------------------

@injected
class EncodingHandler(HandlerBranchingProceed):
    '''
    Implementation for a handler that encodes the response content.
    '''
    
    encodeAssembly = Assembly
    # The encode processors to be used for encoding properties.
    
    def __init__(self):
        assert isinstance(self.encodeAssembly, Assembly), 'Invalid encode assembly %s' % self.encodeAssembly
        super().__init__(Included(self.encodeAssembly).using(encode=Encode))

    def process(self, encodeProcessing, request:Request, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Process the encoder rendering.
        '''
        assert isinstance(encodeProcessing, Processing), 'Invalid processing %s' % encodeProcessing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt

        if response.isSuccess is False: return  # Skip in case the response is in error
        assert isinstance(request.invoker, Invoker), 'Invalid request invoker %s' % request.invoker
        assert callable(response.renderFactory), 'Invalid response renderer factory %s' % response.renderFactory

        response.action = DO_RENDER
        
        output = BytesIO()
        encode = encodeProcessing.ctx.encode()
        assert isinstance(encode, Encode)
        encode.obj = response.obj
        encode.objType = request.invoker.output
        encode.render = response.renderFactory(output)

        if Chain(encodeProcessing).execute(CONSUMED, request=request, response=response, responseCnt=responseCnt,
                                           encode=encode, **keyargs):
            raise DevelError('Cannot encode %s' % request.invoker.output)
        
        content = output.getvalue()
        responseCnt.length = len(content)
        responseCnt.source = (content,)
