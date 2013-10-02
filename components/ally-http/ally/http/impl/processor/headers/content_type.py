'''
Created on Jun 11, 2012

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content type header decoding/encoding.
'''

from ally.container.ioc import injected
from ally.core.http.spec.codes import CONTENT_TYPE_ERROR
from ally.design.processor.attribute import requires, optional, defines, \
    definesIf
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import CodedHTTP
from ally.http.spec.headers import HeadersRequire, CONTENT_TYPE, \
    CONTENT_TYPE_ATTR_CHAR_SET, HeadersDefines
        
# --------------------------------------------------------------------

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)

# --------------------------------------------------------------------

class RequestContentDecode(Context):
    '''
    The request content context decode.
    '''
    # ---------------------------------------------------------------- Defined
    type = defines(str, doc='''
    @rtype: string
    The request content type.
    ''')
    charSet = defines(str, doc='''
    @rtype: string
    The request character set for the text content.
    ''')
    typeAttr = definesIf(dict, doc='''
    @rtype: dictionary{string, string}
    The content request type attributes.
    ''')
    
# --------------------------------------------------------------------

@injected
class ContentTypeRequestDecodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the decoding of content type HTTP request header.
    '''

    def process(self, chain, request:HeadersRequire, requestCnt:RequestContentDecode, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Decode the content type for the request.
        '''
        assert isinstance(requestCnt, RequestContentDecode), 'Invalid request content %s' % requestCnt
        assert isinstance(response, Response), 'Invalid response %s' % response

        value = CONTENT_TYPE.decode(request)
        if not value: return
        
        if len(value) > 1:
            CONTENT_TYPE_ERROR.set(response)
            response.text = 'Invalid value \'%s\' for header \'%s\''\
            ', expected only one type entry' % (value, self.nameContentType)
            return
        
        value, attributes = value[0]
        requestCnt.type = value
        requestCnt.charSet = attributes.get(CONTENT_TYPE_ATTR_CHAR_SET, None)
        if RequestContentDecode.typeAttr in requestCnt: requestCnt.typeAttr = attributes

# --------------------------------------------------------------------

class ResponseContentDecode(Context):
    '''
    The request content context decode.
    '''
    # ---------------------------------------------------------------- Defined
    type = definesIf(str, doc='''
    @rtype: string
    The response content type.
    ''')
    charSet = defines(str, doc='''
    @rtype: string
    The response character set for the text content.
    ''')
    typeAttr = definesIf(dict, doc='''
    @rtype: dictionary{string, string}
    The content response type attributes.
    ''')
    
# --------------------------------------------------------------------

@injected
class ContentTypeResponseDecodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the decoding of content type HTTP response header.
    '''

    def process(self, chain, response:HeadersRequire, responseCnt:ResponseContentDecode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Decode the content type for the response.
        '''
        assert isinstance(responseCnt, ResponseContentDecode), 'Invalid response content %s' % responseCnt
        
        value = CONTENT_TYPE.decode(response)
        if not value: return
        
        if len(value) > 1:
            CONTENT_TYPE_ERROR.set(response)
            response.text = 'Invalid value \'%s\' for header \'%s\''\
            ', expected only one type entry' % (value, self.nameContentType)
            return
        
        value, attributes = value[0]
        if ResponseContentDecode.type in responseCnt:
            responseCnt.type = value
        responseCnt.charSet = attributes.get(CONTENT_TYPE_ATTR_CHAR_SET, None)
        if ResponseContentDecode.typeAttr in responseCnt:
            responseCnt.typeAttr = attributes

# --------------------------------------------------------------------
 
class ResponseContentEncode(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)
    # ---------------------------------------------------------------- Optional
    charSet = optional(str)

# --------------------------------------------------------------------

@injected
class ContentTypeResponseEncodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the encoding of content type HTTP request header.
    '''

    def process(self, chain, response:HeadersDefines, responseCnt:ResponseContentEncode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Encodes the content type for the response.
        '''
        assert isinstance(responseCnt, ResponseContentEncode), 'Invalid response content %s' % responseCnt

        if responseCnt.type:
            value = responseCnt.type
            if ResponseContentEncode.charSet in responseCnt and responseCnt.charSet:
                if responseCnt.charSet: value = (value, {CONTENT_TYPE_ATTR_CHAR_SET: responseCnt.charSet})
            CONTENT_TYPE.encode(response, value)
