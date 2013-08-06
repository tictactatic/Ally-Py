'''
Created on Jul 27, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Renders the response encoder.
'''

from ally.container.ioc import injected
from ally.core.impl.processor.encoder.base import importSupport
from ally.core.spec.transform import ITransfrom
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import Handler, push
from ally.design.processor.processor import Structure, Composite, Using, \
    Contextual
from ally.support.util_context import pushIn, cloneCollection
from collections import Callable

# --------------------------------------------------------------------
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    encoder = requires(ITransfrom)
    
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
class RenderEncoderHandler(Handler):
    '''
    Implementation for a handler that renders the response content encoder.
    '''
    
    encodeExportAssembly = Assembly
    # The encode export assembly.
    
    def __init__(self):
        super().__init__(Using(Composite(push(Contextual(self.process), Invoker=Invoker),
                            Structure(Support=('response', 'request'))), Support=importSupport(self.encodeExportAssembly)))
    
    def process(self, chain, request:Request, response:Response, responseCnt:Context, Support:Context, **keyargs):
        '''
        Process the encoder rendering.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        if response.isSuccess is False: return  # Skip in case the response is in error
        if not request.invoker: return  # No invoker available
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        if not request.invoker.encoder: return  # No encoder to process
        assert isinstance(request.invoker.encoder, ITransfrom), 'Invalid encoder %s' % request.invoker.encoder
        assert callable(response.renderFactory), 'Invalid response renderer factory %s' % response.renderFactory

        support = pushIn(Support(), response, request, interceptor=cloneCollection)
        request.invoker.encoder.transform(response.obj, response.renderFactory(responseCnt), support)
