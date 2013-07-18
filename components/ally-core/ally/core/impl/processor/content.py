'''
Created on Aug 30, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides a processor that provides the request content as an invoking argument.
'''

from ally.api.model import Content
from ally.api.type import Input, typeFor
from ally.container.ioc import injected
from ally.core.impl.processor.assembler.base import InvokerExcluded, \
    RegisterExcluding, excludeFrom
from ally.core.spec.codes import CONTENT_EXPECTED, Coded
from ally.design.processor.attribute import requires, optional, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_context import asData
from ally.support.util_io import IInputStream
from collections import Callable
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    hasContent = requires(bool)
        
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    arguments = requires(dict)

class RequestContentData(Context):
    '''
    The request content context used for the content.
    '''
    # ---------------------------------------------------------------- Optional
    name = optional(str)
    type = optional(str)
    charSet = optional(str)
    length = optional(int)

class RequestContent(RequestContentData):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Required
    source = requires(IInputStream)
    # ---------------------------------------------------------------- Optional
    fetchNextContent = optional(Callable)
    
class InvokerAssembler(InvokerExcluded):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    hasContent = defines(bool, doc='''
    @rtype: boolean
    Flag indicating that the content argument is required for invoker.
    ''')
    solved = defines(set)
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)
    
# --------------------------------------------------------------------

@injected
class ContentHandler(HandlerProcessor):
    '''
    Handler that provides the content as an argument if required.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker)
        
        self.contentType = typeFor(Content)

    def process(self, chain, request:Request, response:Coded, requestCnt:RequestContent=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the content.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Coded), 'Invalid response %s' % response
        
        if response.isSuccess is False: return  # Skip in case the response is in error
        if request.invoker is None: return  # No invoker to provide the scheme for
        
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        if not request.invoker.hasContent: return  # No scheme required
        
        if requestCnt is None or requestCnt.source is None: return CONTENT_EXPECTED.set(response)
        assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
        assert isinstance(requestCnt.source, IInputStream), 'Invalid request content source %s' % requestCnt.source
        
        if request.arguments is None: request.arguments = {}
        request.arguments[self.contentType] = ContentData(requestCnt)

# --------------------------------------------------------------------

class AssemblerContentHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides on the assembly the requirement for the content input.
    '''

    def __init__(self):
        super().__init__(Invoker=InvokerAssembler)
        
        self.contentType = typeFor(Content)

    def process(self, chain, register:RegisterExcluding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the content flag if required.
        '''
        assert isinstance(register, RegisterExcluding), 'Invalid register %s' % register
        if not register.invokers: return  # No invokers to process.
        
        for invoker in register.invokers:
            assert isinstance(invoker, InvokerAssembler), 'Invalid invoker %s' % invoker
            if not invoker.inputs: continue
            
            inpContent, toMany = None, False
            for inp in invoker.inputs:
                assert isinstance(inp, Input), 'Invalid input %s' % inp
                if inp.type == self.contentType:
                    if inpContent is not None: toMany = True
                    inpContent = inp
            
            if toMany:
                log.error('Cannot use because there are to many \'Content\' inputs, only a maximum of one is allowed, at:%s',
                          invoker.location)
                excludeFrom(chain, invoker)
            elif inpContent:
                if invoker.solved is None: invoker.solved = set()
                invoker.solved.add(inpContent.name)
                invoker.hasContent = True

# --------------------------------------------------------------------

class ContentData(Content):
    '''
    A content model based on the request.
    '''
    __slots__ = ('_content', '_closed')

    def __init__(self, content):
        '''
        Construct the content.
        
        @param request: RequestContent
            The request content.
        '''
        assert isinstance(content, RequestContent), 'Invalid request content %s' % content
        assert isinstance(content.source, IInputStream), 'Invalid content source %s' % content.source
        super().__init__(**asData(content, RequestContentData))

        self._content = content
        self._closed = False

    def read(self, nbytes=None):
        '''
        @see: Content.read
        '''
        if self._closed: raise ValueError('I/O operation on a closed content file')
        return self._content.source.read(nbytes)

    def next(self):
        '''
        @see: Content.next
        '''
        if self._closed: raise ValueError('I/O operation on a closed content file')

        self._closed = True
        if RequestContent.fetchNextContent in self._content and self._content.fetchNextContent is not None:
            content = self._content.fetchNextContent()
        else: content = None

        if content is not None: return ContentData(content)
