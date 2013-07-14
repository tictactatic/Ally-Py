'''
Created on Aug 24, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the text base parser processor handler.
'''

from ally.container.ioc import injected
from ally.core.spec.codes import CONTENT_BAD, CONTENT_MISSING, Coded
from ally.core.spec.resources import Converter
from ally.core.spec.transform.encdec import IDecoder, CATEGORY_CONTENT
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_io import IInputStream, IClosable
import abc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    decoder = requires(IDecoder)
    
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    arguments = requires(dict)
    converterContent = requires(Converter)
    
class RequestContent(Context):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)
    charSet = requires(str)
    source = requires(IInputStream)

class Response(Coded):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    errorMessages = defines(list)

class SupportDecoding(Context):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Defined
    category = defines(object, doc='''
    @rtype: object
    The category of the ongoing decoding.
    ''')
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to be used for decoding.
    ''')
    # ---------------------------------------------------------------- Required
    failures = requires(list)

# --------------------------------------------------------------------

@injected
class ParseBaseHandler(HandlerProcessor):
    '''
    Provides the text base renderer.
    '''

    contentTypes = set
    # The set(string) containing as the content types specific for this parser.
    separator = str
    # The separator to be used for path.

    def __init__(self):
        assert isinstance(self.contentTypes, set), 'Invalid content types %s' % self.contentTypes
        assert isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__(Invoker=Invoker)

    def process(self, chain, request:Request, requestCnt:RequestContent, response:Response,
                Support:SupportDecoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Parse the request object.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        # Check if the response is for this parser
        if requestCnt.type in self.contentTypes:
            if requestCnt.source is None: CONTENT_MISSING.set(response)
            else:
                assert isinstance(request.invoker, Invoker), 'Invalid request invoker %s' % request.invoker
                decoder = request.invoker.decoder
                assert isinstance(decoder, IDecoder), 'Invalid decoder %s' % decoder
                assert isinstance(requestCnt.source, IInputStream), 'Invalid request content stream %s' % requestCnt.source
                assert isinstance(requestCnt.charSet, str), 'Invalid request content character set %s' % requestCnt.charSet
    
                support = Support(category=CATEGORY_CONTENT, converter=request.converterContent)
                assert isinstance(support, SupportDecoding), 'Invalid support %s' % support
    
                if request.arguments is None: request.arguments = {}
                errors = self.parse(lambda path, obj: decoder.decode(path, obj, request.arguments, support),
                                    requestCnt.source, requestCnt.charSet)
                if errors is not None or support.failures:
                    CONTENT_BAD.set(response)
                    if response.errorMessages is None: response.errorMessages = []
                    if errors is not None: response.errorMessages.extend(errors)
                    if support.failures: response.errorMessages.extend(support.failures)
                    
                if isinstance(requestCnt.source, IClosable): requestCnt.source.close()
            chain.cancel()  # We need to stop the chain if we have been able to provide the parsing
        else:
            assert log.debug('The content type \'%s\' is not for this %s parser', requestCnt.type, self) or True

    # ----------------------------------------------------------------

    @abc.abstractclassmethod
    def parse(self, decoder, source, charSet):
        '''
        Parse the input stream using the decoder.
        
        @param decoder: callable(path, content) -> list[string]|None
            The decoder to be used by the parsing.
        @param source: IInputStream
            The byte input stream containing the content to be parsed.
        @param charSet: string
            The character set for the input source stream.
        @return: Iterable[string]|None
            If a problem occurred while parsing and decoding it will return a detailed error messages, if the parsing is
            successful a None value will be returned.
        '''
