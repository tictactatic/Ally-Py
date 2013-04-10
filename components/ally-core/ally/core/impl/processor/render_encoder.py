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
from ally.core.spec.transform.index import IIndexer
from ally.core.spec.transform.render import IRender
from ally.design.processor.attribute import requires, defines, optional, \
    definesIf
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from collections import Callable, Iterable
from io import BytesIO
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

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defined
    index = definesIf(str, doc='''
    @rtype: string
    All the indexes for the rendered content.
    ''')
    source = defines(Iterable, doc='''
    @rtype: Iterable
    The generator containing the response content.
    ''')
    length = defines(int)

# --------------------------------------------------------------------

@injected
class RenderEncoderHandler(HandlerProcessorProceed):
    '''
    Implementation for a handler that renders the response content encoder.
    '''
    
    def process(self, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Process the encoder rendering.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt

        if response.isSuccess is False: return  # Skip in case the response is in error
        if response.encoder is None: return  # Skip in case there is no encoder to render
        assert callable(response.renderFactory), 'Invalid response renderer factory %s' % response.renderFactory
        assert isinstance(response.encoder, IEncoder), 'Invalid encoder %s' % response.encoder

        if Response.indexerFactory in response and ResponseContent.index in responseCnt and response.indexerFactory:
            assert callable(response.indexerFactory), 'Invalid response indexer factory %s' % response.indexerFactory
            indexer = response.indexerFactory()
            assert isinstance(indexer, IIndexer), 'Invalid indexer %s created by %s' % (indexer, response.indexerFactory)
        else: indexer = None

        output = BytesIO()
        render = response.renderFactory(output, indexer)
        assert isinstance(render, IRender), 'Invalid render %s' % render
        
        response.encoder.render(response.obj, render, response.support)
        
        content = output.getvalue()
        responseCnt.source = (content,)
        responseCnt.length = len(content)
        output.close()
        if indexer: responseCnt.index = indexer.represent()
        
