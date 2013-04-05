'''
Created on Apr 4, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content index header encoding.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IEncoderHeader

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    encoderHeader = requires(IEncoderHeader)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    index = requires(str)
    
# --------------------------------------------------------------------

@injected
class ContentIndexEncodeHandler(HandlerProcessorProceed):
    '''
    Implementation for a processor that provides the encoding of the index as a header.
    '''
    
    nameIndex = 'Content-Index'
    # The name for the content index header

    def __init__(self):
        assert isinstance(self.nameIndex, str), 'Invalid content index name %s' % self.nameIndex
        super().__init__()

    def process(self, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Encode the index header.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        if not responseCnt.index: return  # There is no index
        assert isinstance(response.encoderHeader, IEncoderHeader), 'Invalid header encoder %s' % response.encoderHeader
        
        response.encoderHeader.encode(self.nameIndex, responseCnt.index)
