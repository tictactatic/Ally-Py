'''
Created on Aug 10, 2011

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the converters for the response content and request content.
'''

from ally.container.ioc import injected
from ally.core.spec.resources import Converter, Normalizer
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Normalized(Context):
    '''
    The normalized content context.
    '''
    # ---------------------------------------------------------------- Defined
    normalizer = defines(Normalizer, doc='''
    @rtype: Normalizer
    The normalizer to use for decoding request content.
    ''')
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for decoding request content.
    ''')
    
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
class NormalizerRequestHandler(HandlerProcessorProceed):
    '''
    Provides the normalizer for the model decoding, this will be populated on the request.
    '''
    normalizer = Normalizer
    # The normalizer to set on the request.

    def __init__(self):
        assert isinstance(self.normalizer, Normalizer), 'Invalid normalizer %s' % self.normalizer
        super().__init__()

    def process(self, request:Normalized, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provide the normalizer for request.
        '''
        assert isinstance(request, Normalized), 'Invalid request %s' % request
        
        request.normalizer = self.normalizer

@injected
class NormalizerResponseHandler(HandlerProcessorProceed):
    '''
    Provides the normalizer for response encoding, this will be populated on the response.
    '''
    normalizer = Normalizer
    # The normalizer to set on the response.

    def __init__(self):
        assert isinstance(self.normalizer, Normalizer), 'Invalid normalizer %s' % self.normalizer
        super().__init__()

    def process(self, response:Normalized, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provide the normalizer for response.
        '''
        assert isinstance(response, Normalized), 'Invalid response %s' % response
        
        response.normalizer = self.normalizer

# --------------------------------------------------------------------

@injected
class ConverterRequestHandler(HandlerProcessorProceed):
    '''
    Provides the converter for the model decoding, this will be populated on the request content.
    '''
    converter = Converter
    # The converter to set on the request.

    def __init__(self):
        assert isinstance(self.converter, Converter), 'Invalid converter %s' % self.converter
        super().__init__()

    def process(self, request:Converted, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provide the character conversion for request and response content.
        '''
        assert isinstance(request, Converted), 'Invalid request %s' % request
        
        request.converter = self.converter

@injected
class ConverterResponseHandler(HandlerProcessorProceed):
    '''
    Provides the converter for response encoding, this will be populated on the response content.
    '''
    converter = Converter
    # The converter to set on the response.

    def __init__(self):
        assert isinstance(self.converter, Converter), 'Invalid converter %s' % self.converter
        super().__init__()

    def process(self, response:Converted, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provide the character conversion for request and response content.
        '''
        assert isinstance(response, Converted), 'Invalid response %s' % response
        
        response.converter = self.converter
