'''
Created on Nov 24, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the processors used in handling the request.
'''

from .definition import definitionError
from .parsing_rendering import assemblyRendering, assemblyParsing, \
    blocksDefinitions
from ally.container import ioc
from ally.core.impl.processor.block_indexing import BlockIndexingHandler
from ally.core.impl.processor.content import ContentHandler
from ally.core.impl.processor.conversion_content import ConverterContentHandler
from ally.core.impl.processor.error_definition import ErrorDefinitionHandler
from ally.core.impl.processor.invoking import InvokingHandler
from ally.core.impl.processor.parsing import ParsingHandler
from ally.core.impl.processor.render_encoder import RenderEncoderHandler
from ally.core.impl.processor.rendering import RenderingHandler
from ally.core.spec.resources import Converter
from ally.design.processor.handler import Handler

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

# --------------------------------------------------------------------

@ioc.entity
def converter() -> Converter: return Converter()

# --------------------------------------------------------------------

@ioc.entity
def rendering() -> Handler:
    b = RenderingHandler()
    b.charSetDefault = default_charset()
    b.renderingAssembly = assemblyRendering()
    return b

@ioc.entity
def converterContent() -> Handler:
    b = ConverterContentHandler()
    b.converter = converter()
    return b

@ioc.entity
def parsing() -> Handler:
    b = ParsingHandler()
    b.charSetDefault = default_charset()
    b.parsingAssembly = assemblyParsing()
    return b

@ioc.entity
def content() -> Handler: return ContentHandler()

@ioc.entity
def invoking() -> Handler: return InvokingHandler()

@ioc.entity
def renderEncoder() -> Handler: return RenderEncoderHandler()

@ioc.entity
def errorDefinition() -> Handler:
    b = ErrorDefinitionHandler()
    b.errors = definitionError()
    return b

# --------------------------------------------------------------------

@ioc.entity
def blockIndexing() -> Handler:
    b = BlockIndexingHandler()
    b.definitions = blocksDefinitions()
    return b
