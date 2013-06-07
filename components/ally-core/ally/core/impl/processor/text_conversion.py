'''
Created on Aug 10, 2011

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the converters for the response content and request content.
'''

from ally.container.ioc import injected
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Converted(Context):
    '''
    The converted content context.
    '''
    # ---------------------------------------------------------------- Defined
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for decoding request content.
    ''')

# --------------------------------------------------------------------

@injected
class ConverterRequestHandler(HandlerProcessor):
    '''
    Provides the converter for the model decoding, this will be populated on the request content.
    '''
    converter = Converter
    # The converter to set on the request.

    def __init__(self):
        assert isinstance(self.converter, Converter), 'Invalid converter %s' % self.converter
        super().__init__()

    def process(self, chain, request:Converted, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the character conversion for request and response content.
        '''
        assert isinstance(request, Converted), 'Invalid request %s' % request
        
        request.converter = self.converter

@injected
class ConverterResponseHandler(HandlerProcessor):
    '''
    Provides the converter for response encoding, this will be populated on the response content.
    '''
    converter = Converter
    # The converter to set on the response.

    def __init__(self):
        assert isinstance(self.converter, Converter), 'Invalid converter %s' % self.converter
        super().__init__()

    def process(self, chain, response:Converted, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the character conversion for request and response content.
        '''
        assert isinstance(response, Converted), 'Invalid response %s' % response
        
        response.converter = self.converter
