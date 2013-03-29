'''
Created on Jan 25, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the text base encoder processor handler.
'''

from ally.container.ioc import injected
from ally.core.spec.transform.render import IPattern
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, \
    HandlerProcessorProceed
from collections import Callable
from functools import partial
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
    @rtype: callable(IOutputStream) -> IRender
    The renderer factory to be used for the response.
    ''')

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)
    charSet = requires(str)

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

            response.renderFactory = partial(self.renderFactory, responseCnt.charSet)
            return  # We need to stop the chain if we have been able to provide the encoding
        chain.proceed()

    # ----------------------------------------------------------------

    @abc.abstractclassmethod
    def renderFactory(self, charSet, output):
        '''
        Factory method used for creating a renderer.
        
        @param charSet: string
            The character set to be used by the created factory.
        @param output: IOutputStream
            The output stream to be used by the renderer.
        @return: IRender
            The renderer.
        '''

# --------------------------------------------------------------------

class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    patterns = defines(dict, doc='''
    @rtype: dictionary{string: Pattern}
    The patterns indexed by pattern unique identifier.
    ''')
    
class PatternSupport(Context):
    '''
    The pattern context.
    '''
    # ---------------------------------------------------------------- Defined
    contentTypes = defines(tuple, doc='''
    @rtype: tuple(string)
    The list of content types to be associated with the pattern.
    ''')
    pattern = defines(IPattern, doc='''
    @rtype: IPattern
    The pattern used for creating captures and matchers.
    ''')
    adjusters = defines(tuple, doc='''
    @rtype: tuple(tuple(string, string))
    A tuple of tuples of two elements, on the first position the regex pattern that is used inside a matcher block
    in order to inject content, on the second position a pattern like string that contain markers
    for using as the replaced value. Markers are like {1}, {2} ... for capture groups from the matcher and like
    //1, //2 ... for capture groups from the replace pattern, this are handled automatically by python regex sub method.
    ''')

# --------------------------------------------------------------------

@injected
class PatternBaseHandler(HandlerProcessorProceed, IPattern):
    '''
    Provides the text base pattern handler.
    '''

    identifier = str
    # The identifier for the represented pattern.
    contentTypes = dict
    # The dictionary{string:string} containing as a key the content types specific for this encoder and as a value
    # the content type to set on the response, if None will use the key for the content type response.
    adjusters = tuple
    # The tuple containing tuples of two that have on the first position the adjuster replace pattern and on the second position
    # the adjuster replace value.

    def __init__(self):
        assert isinstance(self.identifier, str), 'Invalid identifier %s' % self.identifier
        assert isinstance(self.contentTypes, dict), 'Invalid content types %s' % self.contentTypes
        assert isinstance(self.adjusters, tuple), 'Invalid adjusters %s' % self.adjusters
        super().__init__()
        
        self.types = tuple({value or key for key, value in self.contentTypes.items()})
        
    def process(self, Pattern:PatternSupport, support:Support, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Create the pattern support.
        '''
        assert issubclass(Pattern, PatternSupport), 'Invalid pattern class %s' % Pattern
        assert isinstance(support, Support), 'Invalid support %s' % support
        
        if support.patterns is None: support.patterns = {}
        if self.identifier in support.patterns: return  # There is already a pattern for this identifier.
        support.patterns[self.identifier] = Pattern(contentTypes=self.types, pattern=self, adjusters=self.adjusters)
