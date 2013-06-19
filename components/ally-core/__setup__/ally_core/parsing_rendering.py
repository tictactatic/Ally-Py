'''
Created on Nov 24, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setups for the parsing/rendering processors.
'''

from ally.container import ioc
# from ally.core.impl.processor.parser.text import ParseTextHandler
# from ally.core.impl.processor.parser.xml import ParseXMLHandler
from ally.core.impl.processor.render.json import RenderJSONHandler, BLOCKS_JSON
from ally.core.impl.processor.render.xml import RenderXMLHandler, BLOCKS_XML
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
import codecs
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------
# Creating the encoding processors

@ioc.config
def content_types_json() -> dict:
    '''
    The JSON content types, a map that contains as a key the recognized mime type and as a value the normalize mime type,
    if none then the same key mimie type will be used for response
    '''
    return {
            'text/json':None,
            'application/json':None,
            'json':'text/json',
            None:'text/json'
            }

@ioc.config
def content_types_xml() -> dict:
    '''
    The XML content types, a map that contains as a key the recognized mime type and as a value the normalize mime type,
    if none then the same key mimie type will be used for response
    '''
    return {
            'text/xml':None,
            'text/plain':'text/xml',
            'application/xml':None,
            'xml':'text/xml'
            }

@ioc.config
def content_types_yaml() -> dict:
    '''
    The YAML content types, a map that contains as a key the recognized mime type and as a value the normalize mime type,
    if none then the same key mimie type will be used for response.
    '''
    return {
            'text/yaml':None,
            'application/yaml':None,
            'yaml':'text/yaml',
            }

# --------------------------------------------------------------------
# Creating the parsers

@ioc.entity
def assemblyParsing() -> Assembly:
    '''
    The assembly containing the request parsers.
    '''
    return Assembly('Parsing request content')

@ioc.entity
def parseJSON() -> Handler:
    import json
    def parserJSON(content, charSet): return json.load(codecs.getreader(charSet)(content))

    b = ParseTextHandler(); yield b
    b.contentTypes = set(content_types_json())
    b.parser = parserJSON
    b.parserName = 'json'

@ioc.entity
def parseXML() -> Handler:
    b = ParseXMLHandler(); yield b
    b.contentTypes = set(content_types_xml())

# --------------------------------------------------------------------
# Create the renders

@ioc.entity
def assemblyRendering() -> Assembly:
    '''
    The assembly containing the response renders.
    '''
    return Assembly('Renderer response')

@ioc.entity
def blocksDefinitions() -> dict:
    '''
    The indexing blocks definitions.
    '''
    return {}

@ioc.entity
def renderJSON() -> Handler:
    b = RenderJSONHandler(); yield b
    b.contentTypes = content_types_json()

@ioc.entity
def renderXML() -> Handler:
    b = RenderXMLHandler(); yield b
    b.contentTypes = content_types_xml()

# --------------------------------------------------------------------

@ioc.before(blocksDefinitions)
def updateBlocksDefinitions():
    blocksDefinitions().update(BLOCKS_XML)
    blocksDefinitions().update(BLOCKS_JSON)

@ioc.before(assemblyParsing)
def updateAssemblyParsing():
    assemblyParsing().add(parseJSON())
    assemblyParsing().add(parseXML())

@ioc.before(assemblyRendering)
def updateAssemblyRendering():
    assemblyRendering().add(renderJSON())
    assemblyRendering().add(renderXML())
