'''
Created on Feb 4, 2013

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Populates a provided code for the response.
'''

from ally.container.ioc import injected
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import CodedHTTP, CodeHTTP

# --------------------------------------------------------------------

@injected
class DeliverCodeHandler(HandlerProcessor):
    '''
    Handler that just populates a code on the response and then proceeds.
    '''

    code = CodeHTTP
    # The code to deliver

    def __init__(self):
        assert isinstance(self.code, CodeHTTP), 'Invalid code %s' % self.code
        super().__init__()

    def process(self, chain, response:CodedHTTP, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Delivers the code.
        '''
        self.code.set(response)
