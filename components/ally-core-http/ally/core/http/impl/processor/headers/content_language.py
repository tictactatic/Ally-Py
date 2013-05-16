'''
Created on Jun 12, 2012

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content language header decoding.
'''

from ally.api.type import Locale
from ally.container.ioc import injected
from ally.core.http.spec.headers import CONTENT_LANGUAGE
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import HeadersRequire, HeadersDefines

# --------------------------------------------------------------------

class RequestDecode(HeadersRequire):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    language = defines(str, doc='''
    @rtype: string
    The language for the content.
    ''')
    # ---------------------------------------------------------------- Optional
    argumentsOfType = optional(dict)
    
# --------------------------------------------------------------------

@injected
class ContentLanguageDecodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the decoding of content language HTTP request header.
    '''
    
    def process(self, chain, request:RequestDecode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the content language decode for the request.
        '''
        assert isinstance(request, RequestDecode), 'Invalid request %s' % request

        value = CONTENT_LANGUAGE.fetch(request)
        if not value: return
        
        request.language = value
        if RequestDecode.argumentsOfType in request and request.argumentsOfType is not None:
            request.argumentsOfType[Locale] = request.language

# --------------------------------------------------------------------

class ResponseEncode(HeadersDefines):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    language = requires(str)

# --------------------------------------------------------------------

@injected
class ContentLanguageEncodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the encoding of content language HTTP request header.
    '''

    def process(self, chain, response:ResponseEncode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Encodes the content language.
        '''
        assert isinstance(response, ResponseEncode), 'Invalid response %s' % response
        if response.language: CONTENT_LANGUAGE.put(response, response.language)
