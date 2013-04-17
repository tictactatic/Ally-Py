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
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from collections import Callable
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Optional
    indexerFactory = optional(Callable)
    # ---------------------------------------------------------------- Required
    renderFactory = requires(Callable)
    encoder = requires(IEncoder)
    support = requires(object)
    obj = requires(object)
    isSuccess = requires(bool)

# --------------------------------------------------------------------

@injected
class RenderEncoderHandler(HandlerProcessorProceed):
    '''
    Implementation for a handler that renders the response content encoder.
    '''
    
    def process(self, response:Response, responseCnt:Context, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Process the encoder rendering.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response

        if response.isSuccess is False: return  # Skip in case the response is in error
        if response.encoder is None: return  # Skip in case there is no encoder to render
        assert callable(response.renderFactory), 'Invalid response renderer factory %s' % response.renderFactory
        assert isinstance(response.encoder, IEncoder), 'Invalid encoder %s' % response.encoder

        response.encoder.render(response.obj, response.renderFactory(responseCnt), response.support)
