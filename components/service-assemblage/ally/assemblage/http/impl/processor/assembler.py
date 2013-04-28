'''
Created on Mar 27, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assembler processor.
'''

from ally.assemblage.http.spec.assemblage import RequestNode
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context, asData
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.indexing.spec.modifier import Content, IAlter, IModifier
from ally.support.util_io import IInputStream
from collections import Callable, Iterable
import logging
from ally.indexing.impl.modifier import iterateModified

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

ACTION_STREAM = 'stream'  # The action name for streaming a block.
ACTION_DISCARD = 'discard'  # The action name for discarding a block.
ACTION_INJECT = 'inject'  # The action name for injecting in a block.
ACTION_NAME = 'get_name'  # The action name for providing the block name.

ACTION_REFERENCE = 'reference'  # The action name to get the block reference.
ACTION_CHECK_CLOB = 'check_clob'  # The action name to check if the block is for a clob content.
ACTION_ERROR_STATUS = 'error_status'  # The action name for error status.
ACTION_ERROR_MESSAGE = 'error_message'  # The action name for error message.

# --------------------------------------------------------------------

class ResponseContent(Context):
    '''
    The response content context. 
    '''
    # ---------------------------------------------------------------- Defined
    source = defines(Iterable, doc='''
    @rtype: Iterable
    The assembled content source.
    ''')
    
class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Required
    requestNode = requires(RequestNode)
    requestHandler = requires(Callable)
    main = requires(object)

class ContentModifiable(Context):
    '''
    The assemblage modifiable content context.
    '''
    # ---------------------------------------------------------------- Required
    source = requires(IInputStream)
    encode = requires(Callable)
    decode = requires(Callable)
    indexes = requires(list)
    
class ContentResponse(ContentModifiable):
    '''
    The assemblage response content context.
    '''
    # ---------------------------------------------------------------- Required
    errorStatus = requires(int)
    errorText = requires(str)
    
# --------------------------------------------------------------------

@injected
class AssemblerHandler(HandlerProcessor, IAlter):
    '''
    Implementation for a handler that provides the assembling.
    '''
    
    doProcessors = dict
    # The do perform processors used in assembly.
    maximumPackSize = 1024
    # The maximum block size in bytes before dispatching.
    
    def __init__(self):
        assert isinstance(self.doProcessors, dict), 'Invalid do processors %s' % self.doProcessors
        assert isinstance(self.maximumPackSize, int), 'Invalid maximum pack size %s' % self.maximumPackSize
        super().__init__(Content=ContentResponse)

    def process(self, chain, responseCnt:ResponseContent, assemblage:Assemblage, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Assemble response content.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        assert isinstance(assemblage, Assemblage), 'Invalid assemblage %s' % assemblage
        assert isinstance(assemblage.main, ContentResponse), 'Invalid main content %s' % assemblage.main
        assert assemblage.main.errorStatus is None, 'Invalid main content %s, has an error status' % assemblage.main
        
        if not assemblage.main.indexes: return  # No indexes to process
        
        content = ContentAssembly(assemblage.requestHandler, assemblage.requestNode, False,
                                  maximum=self.maximumPackSize, **asData(assemblage.main, ContentModifiable))
        responseCnt.source = iterateModified(self, self.doProcessors, content, ACTION_STREAM)
        chain.proceed()
        
    # --------------------------------------------------------------------
    
    def alter(self, content, modifier):
        '''
        @see: IAlter.alter
        '''
        assert isinstance(content, ContentAssembly), 'Invalid content %s' % content
        assert isinstance(content.node, RequestNode), 'Invalid request node %s' % content.node
        assert isinstance(content.node.requests, dict), 'Invalid requests %s' % content.node.requests
        assert isinstance(modifier, IModifier), 'Invalid modifier %s' % modifier
        
        name = modifier.fetch(ACTION_NAME)
        if name is None: bnode = None
        else: bnode = content.node.requests.get(name)
        if bnode is None: bnode = content.node.requests.get('*')
        if bnode is None:
            if content.isTrimmed: modifier.register(ACTION_DISCARD)
            return
        assert isinstance(bnode, RequestNode), 'Invalid request node %s' % bnode
        
        reference = modifier.fetch(ACTION_REFERENCE)
        if not reference: return  # No reference to process
        if not bnode.requests:
            check = modifier.fetch(ACTION_CHECK_CLOB)
            if not check: return  # Is probably and indexed reference so without requests we continue.
            
        response = content.requestHandler(reference, bnode.parameters)
        assert isinstance(response, ContentResponse), 'Invalid content %s' % response
        if response.errorStatus is not None:
            assert log.debug('Error %s %s for %s', response.errorStatus, response.errorText, reference) or True
            modifier.register(ACTION_ERROR_STATUS, value=str(response.errorStatus))
            modifier.register(ACTION_ERROR_MESSAGE, value=response.errorText)
            return
        
        icontent = ContentAssembly(content.requestHandler, bnode, True,
                                   maximum=content.maximum, **asData(response, ContentModifiable))
        modifier.register(ACTION_INJECT, value=icontent)
    
# --------------------------------------------------------------------

class ContentAssembly(Content):
    '''
    @see: Content extension to provide additional assemblage information.
    '''
    __slots__ = ('requestHandler', 'node', 'isTrimmed')
    
    def __init__(self, requestHandler, node, isTrimmed=True, **keyargs):
        '''
        Construct the content assembly.
        
        @param requestHandler: callable
            The request handler.
        @param node: RequestNode
            The requested nodes for the content.
        @param isTrimmed: boolean
            Flag indicating that the content should be trimmed of unrequested blocks.
        @see: Content.__init__
        '''
        assert callable(requestHandler), 'Invalid request handler %s' % requestHandler
        assert isinstance(node, RequestNode), 'Invalid node %s' % node
        assert isinstance(isTrimmed, bool), 'Invalid is trimmed flag %s' % isTrimmed
        super().__init__(**keyargs)
        
        self.requestHandler = requestHandler
        self.node = node
        self.isTrimmed = isTrimmed
