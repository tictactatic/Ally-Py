'''
Created on Apr 5, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexes for the response content.
'''

from ally.assemblage.http.spec.assemblage import Index, BLOCK, GROUP, INJECT
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
import json

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    headers = requires(dict)

class Content(Context):
    '''
    The assemblage content context.
    '''
    # ---------------------------------------------------------------- Defined
    indexes = defines(list, doc='''
    @rtype: list[Index]
    The list of indexes for the response content.
    ''')
    
# --------------------------------------------------------------------

@injected
class IndexProviderHandler(HandlerProcessorProceed):
    '''
    Provides the index for the content.
    '''
    
    nameIndex = 'Content-Index'
    # The name for the content index header
    
    def __init__(self):
        assert isinstance(self.nameIndex, str), 'Invalid content index name %s' % self.nameIndex
        super().__init__()

    def process(self, response:Response, content:Content, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provide the index for content.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(content, Content), 'Invalid content %s' % content
        
        if not response.headers: return  # No headers available.
        
        value = response.headers.pop(self.nameIndex, None)  # Also making sure not to pass the index header.
        if not value: return  # No content index available for processing.
        indexesJSON = json.loads(value)
        
        indexes, stack = [], []
        for at, mark, value in indexesJSON:
            if mark == 'b': mark = BLOCK
            elif mark == 'g': mark = GROUP
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
        
        if content.indexes is None: content.indexes = indexes
        else: content.indexes.extend(indexes)
