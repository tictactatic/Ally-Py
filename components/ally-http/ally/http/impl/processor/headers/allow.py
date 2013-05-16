'''
Created on Jun 11, 2012

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the allow headers handling.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import METHOD_NOT_AVAILABLE
from ally.http.spec.headers import HeadersDefines, ALLOW

# --------------------------------------------------------------------

class Response(HeadersDefines):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    status = requires(int)
    allows = requires(set)

# --------------------------------------------------------------------

@injected
class AllowEncodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the encoding of allow HTTP request headers.
    '''

    def process(self, chain, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Encode the allow headers.
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response

        if METHOD_NOT_AVAILABLE.status == response.status and response.allows:
            ALLOW.encode(response, *sorted(response.allows))
