'''
Created on Apr 5, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexes for the response content.
'''

from ally.assemblage.http.spec.assemblage import Index, BLOCK, GROUP, LINK, INJECT
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
import json

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    headers = requires(dict)
    
class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defined
    indexes = defines(list, doc='''
    @rtype: list[Index]
    The list of indexes for the response content.
    ''')
    
# --------------------------------------------------------------------

@injected
class IndexProviderHandler(HandlerProcessor):
    '''
    Provides the index for the response content, if no index is available this handler will stop the chain.
    '''
    
    nameIndex = 'Content-Index'
    # The name for the content index header
    
    def __init__(self):
        assert isinstance(self.nameIndex, str), 'Invalid content index name %s' % self.nameIndex
        super().__init__()

    def process(self, chain, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the index for response content.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        if not response.headers: return  # No headers available.
        
        value = response.headers.pop(self.nameIndex, None)  # Also making sure not to pass the index header.
        if not value: return  # No content index available for processing.
        indexesJSON = json.loads(value)
        
        indexes, stack = [], []
        for at, mark, value in indexesJSON:
            if mark == 'b': mark = BLOCK
            elif mark == 'g': mark = GROUP
            elif mark == 'l': mark = LINK
            elif mark == 'i': mark = INJECT
            else:
                assert mark == 'e', 'Unknown mark %s' % mark
                index = stack.pop()
                index.end = at
                mark = None
            
            if mark:
                index = Index(mark, at, value)
                indexes.append(index)
                stack.append(index)
        
        if responseCnt.indexes is None: responseCnt.indexes = indexes
        else: responseCnt.indexes.extend(indexes)
        
        chain.proceed()
