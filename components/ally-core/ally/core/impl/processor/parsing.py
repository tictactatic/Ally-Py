'''
Created on Aug 24, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the parsing chain processors.
'''

from ally.container.ioc import injected
from ally.core.impl.processor.base import ErrorResponse, addError
from ally.core.impl.processor.decoder.base import importTarget
from ally.core.spec.codes import ENCODING_UNKNOWN
from ally.core.spec.resources import Converter
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing, CONSUMED
from ally.design.processor.handler import push, Handler
from ally.design.processor.processor import Brancher, Using
from ally.support.util_spec import IDo
import codecs

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    decodingContent = requires(Context)
    
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    converterContent = requires(Converter)

class RequestContent(Context):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Optional
    doFetchNextContent = optional(IDo)
    # ---------------------------------------------------------------- Required
    type = requires(str)
    charSet = requires(str)

class ResponseContent(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)

class TargetContent(Context):
    '''
    The target context.
    '''
    # ---------------------------------------------------------------- Defined
    arg = defines(object, doc='''
    @rtype: object
    The ongoing chain arguments do decode the parameters based on.
    ''')
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to be used for decoding content.
    ''')

# --------------------------------------------------------------------

@injected
class ParsingHandler(Handler):
    '''
    Implementation for a processor that provides the parsing based on contained parsers. If a parser
    processor is successful in the parsing process it has to stop the chain execution.
    '''

    charSetDefault = str
    # The default character set to be used if none provided for the content.
    decodeExportAssembly = Assembly
    # The decode export assembly.
    parsingAssembly = Assembly
    # The parsers processors, if a processor is successful in the parsing process it has to stop the chain execution.

    def __init__(self):
        assert isinstance(self.charSetDefault, str), 'Invalid default character set %s' % self.charSetDefault
        assert isinstance(self.parsingAssembly, Assembly), 'Invalid parsers assembly %s' % self.parsingAssembly
        Target, arg = importTarget(self.decodeExportAssembly)
        processor = push(Brancher(self.process, Branch(self.parsingAssembly).
                                  included(('decoding', 'Decoding'), ('target', 'Target')).included()), Invoker=Invoker)
        if arg: push(processor, **arg)
        super().__init__(Using(processor, Target=Target))

    def process(self, chain, processing, request:Request, requestCnt:RequestContent, response:ErrorResponse,
                responseCnt:ResponseContent, Target:TargetContent, **keyargs):
        '''
        Parse the request content.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        assert isinstance(response, ErrorResponse), 'Invalid response %s' % response

        if response.isSuccess is False: return  # Skip in case the response is in error
        if not request.invoker: return
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        if not request.invoker.decodingContent: return
        
        target = Target(arg=chain.arg, converter=request.converterContent)
        assert isinstance(target, TargetContent), 'Invalid target %s' % target
        
        # Resolving the character set
        if requestCnt.charSet:
            try: codecs.lookup(requestCnt.charSet)
            except LookupError: requestCnt.charSet = self.charSetDefault
        else: requestCnt.charSet = self.charSetDefault
        if not requestCnt.type: requestCnt.type = responseCnt.type
        
        if not processing.wingIn(chain, True, decoding=request.invoker.decodingContent, target=target).execute(CONSUMED):
            if RequestContent.doFetchNextContent in requestCnt and requestCnt.doFetchNextContent:
                chain.arg.requestCnt = requestCnt.doFetchNextContent()
            else: chain.arg.requestCnt = None
            # We process the chain with the next content or no content.
        elif response.isSuccess is not False:
            ENCODING_UNKNOWN.set(response)
            addError(response, 'Content type \'%(type)s\' not supported for parsing', type=requestCnt.type)
        
