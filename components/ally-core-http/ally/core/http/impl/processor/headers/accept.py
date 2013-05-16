'''
Created on Jun 11, 2012

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the accept headers handling.
'''

from ally.api.type import List, Locale
from ally.container.ioc import injected
from ally.core.http.spec.headers import ACCEPT_LANGUAGE
from ally.design.processor.attribute import optional, defines
from ally.http.impl.processor.headers.accept import RequestDecode, \
    AcceptRequestDecodeHandler

# --------------------------------------------------------------------

LIST_LOCALE = List(Locale)
# The locale list used to set as an additional argument.

# --------------------------------------------------------------------

class Request(RequestDecode):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Optional
    argumentsOfType = optional(dict)
    # ---------------------------------------------------------------- Defined
    accLanguages = defines(list, doc='''
    @rtype: list[string]
    The languages accepted for response.
    ''')

# --------------------------------------------------------------------

@injected
class AcceptDecodeHandler(AcceptRequestDecodeHandler):
    '''
    Implementation for a processor that provides the decoding of accept HTTP request headers.
    '''

    def process(self, chain, request:Request, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Decode the accepted headers.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        super().process(chain, request)
        
        request.accLanguages = ACCEPT_LANGUAGE.decode(request)
        if request.accLanguages:
            if Request.argumentsOfType in request and request.argumentsOfType is not None:
                request.argumentsOfType[LIST_LOCALE] = request.accLanguages
