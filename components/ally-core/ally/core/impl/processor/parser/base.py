'''
Created on Aug 24, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the text base parser processor handler.
'''

from ally.container.ioc import injected
from ally.core.impl.processor.base import ErrorResponse, addError
from ally.core.spec.codes import CONTENT_BAD, CONTENT_MISSING
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_context import findFirst
from ally.support.util_io import IInputStream, IClosable
from ally.support.util_spec import IDo
import abc
import itertools
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    definitions = requires(list)
    
class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Optional
    parent = optional(Context)
    # ---------------------------------------------------------------- Required
    contentDefinitions = requires(dict)
    doDecode = requires(IDo)

class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    category = requires(str)
      
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Context)
    arguments = requires(dict)
    
class RequestContent(Context):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)
    charSet = requires(str)
    source = requires(IInputStream)

class Support(Context):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Defined
    doFailure = defines(IDo, doc='''
    @rtype: callable(Context, object)
    The call to use in reporting content decoding failures.
    ''')
    
# --------------------------------------------------------------------

@injected
class ParseBaseHandler(HandlerProcessor):
    '''
    Provides the text base renderer.
    '''

    contentTypes = set
    # The set(string) containing as the content types specific for this parser.
    category = str
    # The definition category to use for reporting.

    def __init__(self, decoding=Decoding):
        assert isinstance(self.contentTypes, set), 'Invalid content types %s' % self.contentTypes
        assert isinstance(self.category, str), 'Invalid category %s' % self.category
        super().__init__(decoding=decoding, Definition=Definition, Invoker=Invoker)

    def process(self, chain, request:Request, requestCnt:RequestContent, response:ErrorResponse,
                decoding:Context, support:Support, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Parse the request object.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        
        # Check if the response is for this parser
        if requestCnt.type not in self.contentTypes:
            assert log.debug('The content type \'%s\' is not for this %s parser', requestCnt.type, self) or True
            return
        
        chain.cancel()  # We need to stop the chain if we have been able to provide the parsing
        if requestCnt.source is None:
            CONTENT_MISSING.set(response)
            return

        assert isinstance(requestCnt.source, IInputStream), 'Invalid request content stream %s' % requestCnt.source
        assert isinstance(requestCnt.charSet, str), 'Invalid request content character set %s' % requestCnt.charSet
        
        definitions, values, messages = None, None, None
        
        def indexDefinition(decoding):
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            
            defin = findFirst(decoding, Decoding.parent, lambda decoding: decoding.contentDefinitions.get(self.category)
                              if decoding.contentDefinitions else None)
            if defin:
                assert isinstance(defin, Definition), 'Invalid definition %s for %s' % (defin, decoding)
                assert isinstance(defin.name, str), 'Invalid definition name %s' % defin.name
                
                nonlocal definitions
                if definitions is None: definitions = {}
                byName = definitions.get(defin.name)
                if byName is None: byName = definitions[defin.name] = []
                byName.append(defin)
                return defin.name
        
        def doFailure(decoding, value):
            assert value is not None, 'None value is not allowed'
            name = indexDefinition(decoding)
            nonlocal values
            if values is None: values = {}
            byName = values.get(name)
            if byName is None: byName = values[name] = []
            byName.append(value)
            
        support.doFailure = doFailure
        
        def doDecode(decoding, value):
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            assert isinstance(decoding.doDecode, IDo), 'Invalid decode %s' % decoding.doDecode
            assert isinstance(request, Request)
            if request.arguments is None: request.arguments = {}
            decoding.doDecode(value, request.arguments, support)
            
        def doReport(decoding, message):
            assert isinstance(message, str), 'Invalid message %s' % message
            name = indexDefinition(decoding)
            nonlocal messages
            if messages is None: messages = {}
            byName = messages.get(name)
            if byName is None: byName = messages[name] = []
            byName.append(message)
        
        self.parse(requestCnt.source, requestCnt.charSet, decoding, doDecode, doReport)
        
        if definitions or values or messages:
            CONTENT_BAD.set(response)
            
            for name in itertools.chain(sorted(definitions) if definitions else (), (None,)):
                report = []
                if messages and name in messages: report.extend(messages[name])
                
                valuesOfName = values.get(name) if values else None
                if valuesOfName:
                    if name: report.append('Invalid values \'%(values)s\' for \'%(name)s\'')
                    else: report.append('Invalid values \'%(values)s\'')
                    
                if name: report.extend(definitions[name])
                
                addError(response, report, name=name, values=valuesOfName)
                
            if values and None in values or messages and None in messages:
                categoryDefinitions = []
                for defin in request.invoker.definitions:
                    assert isinstance(defin, Definition), 'Invalid definition %s' % defin
                    if defin.category == self.category: categoryDefinitions.append(defin)
                if categoryDefinitions: addError(response, 'The available content', categoryDefinitions)
            
        if isinstance(requestCnt.source, IClosable): requestCnt.source.close()

    # ----------------------------------------------------------------

    @abc.abstractclassmethod
    def parse(self, source, charSet, definition, doDecode, doReport):
        '''
        Parse the input stream using the decoder.
        
        @param source: IInputStream
            The byte input stream containing the content to be parsed.
        @param charSet: string
            The character set for the input source stream.
        @param definition: Definition
            The definition to be used by the parsing.
        @param doDecode: callable(decoding, object)
            The decode to be used by the parsing, the first argument is the decoding to decode
            and the second one is the value to be decoded.
        @param doReport: callable(decoding, string)
            The report decoding to be used by the parsing, the first argument is the decoding target
            and the second one is the error message.
        '''
