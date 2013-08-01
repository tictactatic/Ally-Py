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
from ally.design.processor.attribute import requires, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_context import findFirst
from ally.support.util_io import IInputStream, IClosable
from ally.support.util_spec import IDo
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
    
class RequestContent(Context):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)
    charSet = requires(str)
    source = requires(IInputStream)

class Target(Context):
    '''
    The target context.
    '''
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
    category = str
    # The definition category to use for reporting.

    def __init__(self, decoding=Decoding):
        assert isinstance(self.contentTypes, set), 'Invalid content types %s' % self.contentTypes
        assert isinstance(self.category, str), 'Invalid category %s' % self.category
        super().__init__(decoding=decoding, Definition=Definition, Invoker=Invoker)

    def process(self, chain, request:Request, requestCnt:RequestContent, response:ErrorResponse,
                decoding:Context, target:Target, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Parse the request object.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
        assert isinstance(target, Target), 'Invalid support %s' % target
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
        
        self.parse(requestCnt.source, requestCnt.charSet, decoding, target)
        
        if target.failures:
            CONTENT_BAD.set(response)
            
            for name, definitions, values, messages in self.indexFailures(target.failures):
                if values:
                    if name: messages.append('Invalid values \'%(values)s\' for \'%(name)s\'')
                    else: messages.append('Invalid values \'%(values)s\'')
                
                addError(response, messages, definitions, name=name, values=values)
                
                if not name:
                    defins = []
                    for defin in request.invoker.definitions:
                        assert isinstance(defin, Definition), 'Invalid definition %s' % defin
                        if defin.category == self.category: defins.append(defin)
                    if defins: addError(response, 'The available content', defins)
            
        if isinstance(requestCnt.source, IClosable): requestCnt.source.close()

    # --------------------------------------------------------------------
    
    def indexFailures(self, failures):
        '''
        Indexes the failures, iterates (name, definitions, values, messages)
        '''
        assert isinstance(failures, list), 'Invalid failures %s' % failures
        
        indexed = {}
        for decoding, value, messages, data in failures:
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            
            defin = findFirst(decoding, Decoding.parent, lambda decoding: decoding.contentDefinitions.get(self.category)
                              if decoding.contentDefinitions else None)
            if defin:
                assert isinstance(defin, Definition), 'Invalid definition %s for %s' % (defin, decoding)
                assert isinstance(defin.name, str), 'Invalid definition name %s' % defin.name
                name = defin.name
            else: name = None
                
            byName = indexed.get(name)
            if byName is None: byName = indexed[name] = ([], [], [])
            defins, values, msgs = byName
            if defin: defins.append(defin)
            if value: values.append(value)
            msgs.extend(msg % data for msg in messages)
        
        last = indexed.pop(None, None)
        for name in sorted(indexed):
            yield (name,) + indexed[name]
        if last:
            yield (None,) + last
            
    # ----------------------------------------------------------------

    @abc.abstractclassmethod
    def parse(self, source, charSet, decoding, target):
        '''
        Parse the input stream using the decoder.
        
        @param source: IInputStream
            The byte input stream containing the content to be parsed.
        @param charSet: string
            The character set for the input source stream.
        @param decoding: Decoding
            The decoding to be used by the parsing.
        @param target: Target
            The target to decode in.
        '''
