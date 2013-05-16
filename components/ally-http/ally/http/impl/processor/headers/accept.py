'''
Created on Jun 11, 2012

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the accept headers handling.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import ACCEPT, HeadersRequire, ACCEPT_CHARSET, \
    HeadersDefines
    
# --------------------------------------------------------------------

class RequestDecode(HeadersRequire):
    '''
    The request decode context.
    '''
    # ---------------------------------------------------------------- Defined
    accTypes = defines(list, doc='''
    @rtype: list[string]
    The content types accepted for response.
    ''')
    accCharSets = defines(list, doc='''
    @rtype: list[string]
    The character sets accepted for response.
    ''')

# --------------------------------------------------------------------

@injected
class AcceptRequestDecodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the decoding of accept HTTP request headers.
    '''

    def process(self, chain, request:RequestDecode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Decode the accepted headers.
        '''
        assert isinstance(request, RequestDecode), 'Invalid request %s' % request

        request.accTypes = ACCEPT.decode(request)
        request.accCharSets = ACCEPT_CHARSET.decode(request)

# --------------------------------------------------------------------

class RequestEncode(HeadersDefines):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    accTypes = requires(list)
    accCharSets = requires(list)

# --------------------------------------------------------------------

@injected
class AcceptRequestEncodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the encoding of accept HTTP request headers.
    '''
    
    def process(self, chain, request:RequestEncode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Encode the accepted headers.
        '''
        assert isinstance(request, RequestEncode), 'Invalid request %s' % request

        if request.accTypes: ACCEPT.encode(request, *request.accTypes)
        if request.accCharSets: ACCEPT_CHARSET.encode(request, *request.accCharSets)
