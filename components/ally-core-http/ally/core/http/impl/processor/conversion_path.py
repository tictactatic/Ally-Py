'''
Created on Aug 10, 2011

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the converter for path.
'''

from ally.container.ioc import injected
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    converterPath = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for decoding or encoding path.
    ''')

# --------------------------------------------------------------------

@injected
class ConverterPathHandler(HandlerProcessor):
    '''
    Provides the converter for the path decoding, this will be populated on the request.
    '''
    converter = Converter
    # The converter to set on the request.

    def __init__(self):
        assert isinstance(self.converter, Converter), 'Invalid converter %s' % self.converter
        super().__init__()

    def process(self, chain, request:Request, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the character conversion for request path.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        
        request.converterPath = self.converter

