'''
Created on Jan 25, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the text base encoder processor handler.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_io import IInputStream
from collections import Callable
import abc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    renderFactory = defines(Callable, doc='''
    @rtype: callable(Content, markers=None) -> IRender
    The renderer factory to be used for the response content, it receives as the first argument the content to render in
    and as the second argument is an optional one and provides the markers to be used in the rendering indexing, if not
    provided then no indexing will occur. 
    ''')
    
class Content(Context):
    '''
    The content context.
    '''
    # ---------------------------------------------------------------- Defined
    source = defines(IInputStream)
    length = defines(int)
    indexes = defines(list, doc='''
    @rtype: list[Index]
    The indexes list.
    ''')
    # ---------------------------------------------------------------- Required
    charSet = requires(str)

class ResponseContent(Content):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)

# --------------------------------------------------------------------

@injected
class RenderBaseHandler(HandlerProcessor):
    '''
    Provides the text base renderer.
    '''

    contentTypes = dict
    # The dictionary{string:string} containing as a key the content types specific for this encoder and as a value
    # the content type to set on the response, if None will use the key for the content type response.

    def __init__(self):
        assert isinstance(self.contentTypes, dict), 'Invalid content types %s' % self.contentTypes
        super().__init__()

    def process(self, chain, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the renderer factory
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt

        # Check if the response is for this encoder
        if responseCnt.type not in self.contentTypes:
            assert log.debug('The content type \'%s\' is not for this %s encoder', responseCnt.type, self) or True
        else:
            contentType = self.contentTypes[responseCnt.type]
            if contentType:
                assert log.debug('Normalized content type \'%s\' to \'%s\'', responseCnt.type, contentType) or True
                responseCnt.type = contentType

            response.renderFactory = self.renderFactory
            chain.cancel()  # We need to stop the chain if we have been able to provide the encoding

    # ----------------------------------------------------------------

    @abc.abstractclassmethod
    def renderFactory(self, content):
        '''
        Factory method used for creating a renderer for the provided content.
        
        @param content: Content
            The content to render in.
        @return: IRender
            The renderer for the content.
        '''
