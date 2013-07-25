'''
Created on Aug 24, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the XML parser processor handler.
'''

from . import base
from .base import ParseBaseHandler
from ally.container.ioc import injected
from ally.design.processor.attribute import requires
from ally.support.util_io import IInputStream
from xml.sax import make_parser
from xml.sax._exceptions import SAXParseException
from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import InputSource
import itertools

# --------------------------------------------------------------------

class Decoding(base.Decoding):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    children = requires(dict)
    
# --------------------------------------------------------------------

@injected
class ParseXMLHandler(ParseBaseHandler):
    '''
    Provides the XML parsing.
    @see: ParseBaseHandler
    '''

    def __init__(self):
        super().__init__(decoding=Decoding)

        self.parser = make_parser()

    def parse(self, source, charSet, decoding, doDecode, doReport):
        '''
        @see: ParseBaseHandler.parse
        '''
        assert isinstance(source, IInputStream), 'Invalid stream %s' % source
        assert isinstance(charSet, str), 'Invalid character set %s' % charSet
        
        parse = Parse(self.parser, decoding, doDecode, doReport)
        self.parser.setContentHandler(parse)
        inpsrc = InputSource()
        inpsrc.setByteStream(source)
        inpsrc.setEncoding(charSet)
        try: self.parser.parse(source)
        except SAXParseException as e:
            assert isinstance(e, SAXParseException)
            doReport(decoding, 'Bad XML content at line %s and column %s' % (e.getLineNumber(), e.getColumnNumber()))

# --------------------------------------------------------------------

class Parse(ContentHandler):
    '''
    Content handler used for parsing the xml content.
    '''
    __slots__ = ('parser', 'decoding', 'doDecode', 'doReport', 'last', 'isInvalid', 'path', 'content', 'contains')

    def __init__(self, parser, decoding, doDecode, doReport):
        '''
        Construct the parser.
        
        @param parser: object
            The XML parser.
        @param definition: DefinitionXML
            The decoder definition used in the parsing process.
        '''
        assert parser is not None, 'A parser is required'
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        super().__init__()
        
        self.parser = parser
        self.decoding = decoding
        self.doDecode = doDecode
        self.doReport = doReport

        self.last = decoding
        self.isInvalid = False
        self.path = []
        self.content = []
        self.contains = [False]

    def startElement(self, name, attributes):
        '''
        @see: ContentHandler.startElement
        '''
        if self.isInvalid:
            self.path.append(name)
            return
        
        if self.path:
            isUnexpected = not self.last.children or name not in self.last.children
            if isUnexpected:
                self.isInvalid = True
                self.path.append(name)
            else:
                self.last = self.last.children[name]
                self.path.append(self.last)
        else:
            isUnexpected = name != self.last.name
            if isUnexpected:
                self.isInvalid = True
                self.path.append(name)
            else:
                self.path.append(self.last)
            
        if isUnexpected:
            self.doReport(self.last, 'Unexpected element \'%s\' at line %s and column %s' % 
                          self.located(asPath(self.path)))
        elif attributes:
            self.doReport(self.last, 'No attributes accepted for \'%s\' at line %s and column %s' % 
                          self.located(asPath(self.path)))

        if self.isInvalid: return
            
        self.content.append([])
        self.contains[-1] = True
        self.contains.append(False)

    def characters(self, content):
        '''
        @see: ContentHandler.characters
        '''
        if not self.isInvalid: self.content[-1].append(content)

    def endElement(self, name):
        '''
        @see: ContentHandler.endElement
        '''
        if not self.path:
            self.doReport(self.last, 'Unexpected end element \'%s\' at line %s and column %s' % self.located(name))
            return
        
        current = self.path.pop()
        previous = self.path[-1] if self.path else self.decoding
        if self.isInvalid:
            if self.last == previous: self.isInvalid = False
            return
        
        assert isinstance(current, Decoding), 'Invalid decoding %s' % current
        self.last = previous

        contains = self.contains.pop()
        if contains:
            content = ''.join(self.content.pop()).strip()
            if content:
                self.doReport(current, 'Invalid value \'%s\' for element \'%s\' at line %s and column %s' % 
                              self.located(content, asPath(self.path, name)))
        else:
            content = '\n'.join(self.content.pop())
            if content.strip(): self.doDecode(current, content)
            else: self.doReport(current, 'Expected a value for element \'%s\' at line %s and column %s' % 
                                self.located(asPath(self.path, name)))

    # ----------------------------------------------------------------
    
    def located(self, *args):
        '''
        Provides a tuple with the line and column at the end of the provided arguments
        '''
        return args + (self.parser.getLineNumber(), self.parser.getColumnNumber())
    
# --------------------------------------------------------------------

def asPath(elements, *extra):
    '''
    Construct the XPath based on path elements.
    '''
    assert isinstance(elements, list), 'Invalid path elements %s' % elements
    path = []
    for item in itertools.chain(elements, extra):
        if isinstance(item, str): path.append(item)
        else:
            assert isinstance(item, Decoding), 'Invalid decoding %s' % item
            path.append(item.name)
    return '/'.join(path)
