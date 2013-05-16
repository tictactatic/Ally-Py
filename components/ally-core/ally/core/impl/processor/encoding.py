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
from ally.core.spec.transform.encoder import IEncoder
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context, pushIn
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.exception import DevelError
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
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder to be used for rendering the response object.
    ''')
    support = defines(object, doc='''
    @rtype: object
    The support object required in encoding.
    ''')
    # ---------------------------------------------------------------- Required
    isSuccess = requires(bool)

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    objType = defines(object, doc='''
    @rtype: object
    The object type.
    ''')
    # ---------------------------------------------------------------- Required
    encoder = requires(IEncoder)
    
# --------------------------------------------------------------------

@injected
class EncodingHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the creation of encoders for response objects.
    '''
    
    encodeAssembly = Assembly
    # The encode processors to be used for encoding properties.
    
    def __init__(self):
        assert isinstance(self.encodeAssembly, Assembly), 'Invalid encode assembly %s' % self.encodeAssembly
        super().__init__(Branch(self.encodeAssembly).
                         using(('support', 'response'), ('support', 'request'), create=Create).included())

    def process(self, chain, encodeProcessing, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Process the encoder rendering.
        '''
        assert isinstance(encodeProcessing, Processing), 'Invalid processing %s' % encodeProcessing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response

        if response.isSuccess is False: return  # Skip in case the response is in error
        if response.encoder: return  # There is already an encoder no need to create another one
        assert isinstance(request.invoker, Invoker), 'Invalid request invoker %s' % request.invoker
        
        arg = encodeProcessing.execute(create=encodeProcessing.ctx.create(objType=request.invoker.output),
                                       support=pushIn(encodeProcessing.ctx.support(), response, request), **keyargs)
        assert isinstance(arg.create, Create), 'Invalid create %s' % arg.create
        if arg.create.encoder is not None:
            response.encoder = arg.create.encoder
            response.support = arg.support
