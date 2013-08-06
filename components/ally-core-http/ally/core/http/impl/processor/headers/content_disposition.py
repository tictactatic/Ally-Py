'''
Created on Jun 11, 2012

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content disposition header decoding.
'''

from ally.container.ioc import injected
from ally.core.http.impl.processor.base import ErrorResponseHTTP
from ally.core.http.spec.headers import CONTENT_DISPOSITION, \
    CONTENT_DISPOSITION_ATTR_FILENAME
from ally.core.impl.processor.base import addError
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import HEADER_ERROR
from ally.http.spec.headers import HeadersRequire

# --------------------------------------------------------------------

class RequestContent(Context):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The content name.
    ''')
    disposition = defines(str, doc='''
    @rtype: string
    The content disposition.
    ''')
    dispositionAttr = defines(dict, doc='''
    @rtype: dictionary{string, string}
    The content disposition attributes.
    ''')

class Response(ErrorResponseHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)

# --------------------------------------------------------------------

@injected
class ContentDispositionDecodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the decoding of content disposition HTTP request header.
    '''

    def process(self, chain, request:HeadersRequire, requestCnt:RequestContent, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process

        Provides the content type decode for the request.
        '''
        assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(request.headers, dict), 'Invalid headers %s' % request.headers

        value = CONTENT_DISPOSITION.decode(request)
        if value:
            if len(value) > 1:
                if response.isSuccess is False: return  # Skip in case the response is in error
                HEADER_ERROR.set(response)
                response.text = 'Invalid \'%s\'' % CONTENT_DISPOSITION.name
                addError('Invalid value \'%(value)s\' for header \'%(header)s\', expected only one value entry',
                         value=value, header=CONTENT_DISPOSITION.name)
                return
            value, attributes = value[0]
            requestCnt.disposition = value
            requestCnt.dispositionAttr = attributes
            if self.uploadFilename in attributes:
                requestCnt.name = attributes[CONTENT_DISPOSITION_ATTR_FILENAME]
