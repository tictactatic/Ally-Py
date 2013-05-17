'''
Created on Nov 24, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the processors used in handling the request.
'''

from .encode import assemblyEncode
from .parsing_rendering import assemblyRendering, assemblyParsing, \
    blocksDefinitions
from ally.container import ioc
from ally.core.impl.processor.arguments import ArgumentsPrepareHandler, \
    ArgumentsBuildHandler
from ally.core.impl.processor.content import ContentHandler
from ally.core.impl.processor.decoder import CreateDecoderHandler
from ally.core.impl.processor.encoding import EncodingHandler
from ally.core.impl.processor.invoking import InvokingHandler
from ally.core.impl.processor.parsing import ParsingHandler
from ally.core.impl.processor.render_encoder import RenderEncoderHandler
from ally.core.impl.processor.rendering import RenderingHandler
from ally.core.impl.processor.text_conversion import NormalizerRequestHandler, \
    ConverterRequestHandler, NormalizerResponseHandler, ConverterResponseHandler
from ally.core.spec.resources import Normalizer, Converter
from ally.design.processor.handler import Handler
from ally.core.impl.processor.block_indexing import BlockIndexingHandler
from ally.core.impl.processor.option_slice import OptionSliceHandler

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.config
def default_language() -> str:
    '''The default language to use in case none is provided in the request'''
    return 'en'

@ioc.config
def default_charset() -> str:
    '''The default character set to use if none is provided in the request'''
    return 'UTF-8'

@ioc.config
def explain_detailed_error() -> bool:
    '''If True will provide as an error response a detailed response containing info about where the problem originated'''
    return True

@ioc.config
def slice_limit_maximum() -> int:
    ''' The maximum imposed slice limit on a collection, if none then no maximum limit will be imposed'''
    return 100

@ioc.config
def slice_limit_default() -> int:
    '''
    The default slice limit on a collection if none is specified, if none then the 'slice_limit_maximum' limit
    will be used as the default one.
    '''
    return 30

@ioc.config
def slice_with_total() -> bool:
    ''' The default value for providing the total count'''
    return True

# --------------------------------------------------------------------

@ioc.entity
def normalizer() -> Normalizer: return Normalizer()

@ioc.entity
def converter() -> Converter: return Converter()

# --------------------------------------------------------------------

@ioc.entity
def argumentsPrepare() -> Handler: return ArgumentsPrepareHandler()

@ioc.entity
def rendering() -> Handler:
    b = RenderingHandler()
    b.charSetDefault = default_charset()
    b.renderingAssembly = assemblyRendering()
    return b

@ioc.entity
def normalizerRequest() -> Handler:
    b = NormalizerRequestHandler()
    b.normalizer = normalizer()
    return b

@ioc.entity
def converterRequest() -> Handler:
    b = ConverterRequestHandler()
    b.converter = converter()
    return b

@ioc.entity
def normalizerResponse() -> Handler:
    b = NormalizerResponseHandler()
    b.normalizer = normalizer()
    return b

@ioc.entity
def converterResponse() -> Handler:
    b = ConverterResponseHandler()
    b.converter = converter()
    return b

@ioc.entity
def encoding() -> Handler:
    b = EncodingHandler()
    b.encodeAssembly = assemblyEncode()
    return b

@ioc.entity
def createDecoder() -> Handler: return CreateDecoderHandler()

@ioc.entity
def parsing() -> Handler:
    b = ParsingHandler()
    b.charSetDefault = default_charset()
    b.parsingAssembly = assemblyParsing()
    return b

@ioc.entity
def content() -> Handler: return ContentHandler()

@ioc.entity
def argumentsBuild() -> Handler: return ArgumentsBuildHandler()

@ioc.entity
def optionSlice() -> Handler:
    b = OptionSliceHandler()
    b.maximumLimit = slice_limit_maximum()
    b.defaultLimit = slice_limit_default()
    b.defaultWithTotal = slice_with_total()
    return b

@ioc.entity
def invoking() -> Handler: return InvokingHandler()

@ioc.entity
def renderEncoder() -> Handler: return RenderEncoderHandler()

# --------------------------------------------------------------------

@ioc.entity
def blockIndexing() -> Handler:
    b = BlockIndexingHandler()
    b.definitions = blocksDefinitions()
    return b
