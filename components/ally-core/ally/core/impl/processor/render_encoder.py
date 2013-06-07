'''
Created on Jul 27, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Renders the response encoder.
'''

from ally.container.ioc import injected
from ally.core.spec.transform.encoder import IEncoder
from ally.design.processor.attribute import requires, optional
from ally.design.processor.context import Context, pushIn, cloneCollection
from ally.design.processor.handler import HandlerComposite
from ally.design.processor.processor import Joiner
from collections import Callable

# --------------------------------------------------------------------
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    encoder = requires(IEncoder)
    
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    
class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Optional
    indexerFactory = optional(Callable)
    # ---------------------------------------------------------------- Required
    renderFactory = requires(Callable)
    obj = requires(object)
    isSuccess = requires(bool)

# --------------------------------------------------------------------

@injected
class RenderEncoderHandler(HandlerComposite):
    '''
    Implementation for a handler that renders the response content encoder.
    '''
    
    def __init__(self):
        super().__init__(Joiner(Support=('response', 'request')), Invoker=Invoker)
    
    def process(self, chain, request:Request, response:Response, responseCnt:Context, Support:Context, **keyargs):
        '''
        @see: HandlerComposite.process
        
        Process the encoder rendering.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        if response.isSuccess is False: return  # Skip in case the response is in error
        if not request.invoker: return  # No invoker available
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        if not request.invoker.encoder: return  # No encoder to process
        assert isinstance(request.invoker.encoder, IEncoder), 'Invalid encoder %s' % request.invoker.encoder
        assert callable(response.renderFactory), 'Invalid response renderer factory %s' % response.renderFactory
        
        renderer = response.renderFactory(responseCnt)
        support = pushIn(Support(), response, request, interceptor=cloneCollection)
        request.invoker.encoder.render(response.obj, renderer, support)
