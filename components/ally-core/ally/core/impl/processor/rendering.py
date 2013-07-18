'''
Created on Jul 12, 2011

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the rendering processing.
'''

from ally.container.ioc import injected
from ally.core.impl.processor.base import ErrorResponse, addError
from ally.core.spec.codes import ENCODING_UNKNOWN
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, optional
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing, CONSUMED
from ally.design.processor.handler import HandlerBranching
import codecs
import itertools

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Optional
    accTypes = optional(list)
    accCharSets = optional(list)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defined
    type = defines(str, doc='''
    @rtype: string
    The response content type.
    ''')
    charSet = defines(str, doc='''
    @rtype: string
    The character set for the text content.
    ''')

# --------------------------------------------------------------------

@injected
class RenderingHandler(HandlerBranching):
    '''
    Implementation for a processor that provides the support for creating the renderer. If a processor is successful
    in the render creation process it has to stop the chain execution.
    '''

    contentTypeDefaults = [None]
    # The default content types to use
    charSetDefault = str
    # The default character set to be used if none provided for the content.
    renderingAssembly = Assembly
    # The render processors, if a processor is successful in the rendering factory creation process it has to stop the 
    # chain execution.

    def __init__(self):
        assert isinstance(self.renderingAssembly, Assembly), 'Invalid renders assembly %s' % self.renderingAssembly
        assert isinstance(self.contentTypeDefaults, (list, tuple)), \
        'Invalid default content type %s' % self.contentTypeDefaults
        assert isinstance(self.charSetDefault, str), 'Invalid default character set %s' % self.charSetDefault
        super().__init__(Branch(self.renderingAssembly).included())

    def process(self, chain, processing, request:Request, response:ErrorResponse, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the render for the response object.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        # Resolving the character set
        if responseCnt.charSet:
            try: codecs.lookup(responseCnt.charSet)
            except LookupError: responseCnt.charSet = None
        else: responseCnt.charSet = None

        if not responseCnt.charSet:
            if Request.accCharSets in request and request.accCharSets is not None:
                for charSet in request.accCharSets:
                    try: codecs.lookup(charSet)
                    except LookupError: continue
                    responseCnt.charSet = charSet
                    break
            if not responseCnt.charSet: responseCnt.charSet = self.charSetDefault

        resolved = False
        if responseCnt.type:
            if chain.branch(processing).execute(CONSUMED):
                if response.isSuccess is not False:
                    ENCODING_UNKNOWN.set(response)
                    addError(response, 'Content type \'%(type)s\' not supported for rendering', type=responseCnt.type)
            else: resolved = True

        if not resolved:
            # Adding None in case some encoder is configured as default.
            if Request.accTypes in request and request.accTypes is not None:
                contentTypes = itertools.chain(request.accTypes, self.contentTypeDefaults)
            else: contentTypes = self.contentTypeDefaults
            for contentType in contentTypes:
                responseCnt.type = contentType
                if not chain.branch(processing).execute(CONSUMED): break
            else:
                ENCODING_UNKNOWN.set(response)
                addError(response,
                         'There is no renderer available',
                         'This is more likely a setup issues since the default content types should have resolved the renderer')
