'''
Created on Jun 5, 2012

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides support for setting fixed headers on responses.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import HeadersDefines, encode
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    method = requires(str)

# --------------------------------------------------------------------

@injected
class HeadersSetHandler(HandlerProcessor):
    '''
    Provides the setting of static header values.
    '''

    headers = dict
    # The static header values to set on the response is of type dictionary{string, list[string]}

    def __init__(self):
        assert isinstance(self.headers, dict), 'Invalid header dictionary %s' % self.header
        if __debug__:
            for name, values in self.headers.items():
                assert isinstance(name, str), 'Invalid header name %s' % name
                assert isinstance(values, list), 'Invalid header values %s' % values
                for value in values: assert isinstance(value, str), 'Invalid values item %s' % value
        super().__init__()

    def process(self, chain, response:HeadersDefines, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Set the fixed header values on the response.
        '''
        for name, values in self.headers.items(): encode(response, name, *values)
