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
from ally.design.processor.branch import Using
from ally.design.processor.context import Context, pushIn
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranchingProceed
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
class EncodingHandler(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the creation of encoders for response objects.
    '''
    
    encodeAssembly = Assembly
    # The encode processors to be used for encoding properties.
    
    def __init__(self):
        assert isinstance(self.encodeAssembly, Assembly), 'Invalid encode assembly %s' % self.encodeAssembly
        super().__init__(Using(self.encodeAssembly, ('support', 'response'), ('support', 'request'), create=Create))

    def process(self, encodeProcessing, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Process the encoder rendering.
        '''
        assert isinstance(encodeProcessing, Processing), 'Invalid processing %s' % encodeProcessing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response

        if response.isSuccess is False: return  # Skip in case the response is in error
        if response.encoder: return  # There is already an encoder no need to create another one
        assert isinstance(request.invoker, Invoker), 'Invalid request invoker %s' % request.invoker
        
        # TODO: Gabriel: remove
        print('support:', list(encodeProcessing.ctx.support.__attributes__))
        print('request:', list(request.__attributes__))
        print('response:', list(response.__attributes__))
        print(request)
        supp = encodeProcessing.ctx.support()
        print(pushIn(supp, response, request))
        
        chain = Chain(encodeProcessing)
        chain.process(create=encodeProcessing.ctx.create(objType=request.invoker.output),
                      support=pushIn(encodeProcessing.ctx.support(), response, request)).doAll()
        create, support = chain.arg.create, chain.arg.support
        assert isinstance(create, Create), 'Invalid create %s' % create
        if create.encoder is None: raise DevelError('Cannot encode response object \'%s\'' % request.invoker.output)
        
        response.encoder = create.encoder
        response.support = support
