'''
Created on Aug 10, 2011

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the converter for content.
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
    converterContent = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for decoding or encoding content.
    ''')

# --------------------------------------------------------------------

@injected
class ConverterContentHandler(HandlerProcessor):
    '''
    Provides the converter for the content decoding, this will be populated on the request.
    '''
    converter = Converter
    # The converter to set on the request.

    def __init__(self):
        assert isinstance(self.converter, Converter), 'Invalid converter %s' % self.converter
        super().__init__()

    def process(self, chain, request:Request, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the character conversion for content.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        
        request.converterContent = self.converter

