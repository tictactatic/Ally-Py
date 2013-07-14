'''
Created on Aug 24, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the XML parser processor handler.
'''

from .base import ParseBaseHandler
from ally.container.ioc import injected
from ally.support.util_io import IInputStream
from collections import deque
from xml.sax import make_parser
from xml.sax._exceptions import SAXParseException
from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import InputSource

# --------------------------------------------------------------------

@injected
class ParseXMLHandler(ParseBaseHandler):
    '''
    Provides the XML parsing.
    @see: ParseBaseHandler
    '''

    def __init__(self):
        super().__init__()

        self.parser = make_parser()

    def parse(self, decoder, source, charSet):
        '''
        @see: ParseBaseHandler.parse
        '''
        assert isinstance(source, IInputStream), 'Invalid stream %s' % source
        assert isinstance(charSet, str), 'Invalid character set %s' % charSet
        
        parse = Parse(self.parser, decoder, self.separator)
        self.parser.setContentHandler(parse)
        inpsrc = InputSource()
        inpsrc.setByteStream(source)
        inpsrc.setEncoding(charSet)
        try: self.parser.parse(source)
        except SAXParseException as e:
            assert isinstance(e, SAXParseException)
            parse.report('Bad XML content at line %s and column %s' % (e.getLineNumber(), e.getColumnNumber()))
        return parse.errors

# --------------------------------------------------------------------

class Parse(ContentHandler):
    '''
    Content handler used for parsing the xml content.
    '''
    __slots__ = ('parser', 'decoder', 'path', 'content', 'error')

    def __init__(self, parser, decoder, separator):
        '''
        Construct the parser.
        
        @param parser: object
            The XML parser.
        @param decoder: callable(path, content) -> list[string]|None
            The decoder used in the parsing process.
        @param separator: string
            The separator to be used for path.
        '''
        assert parser is not None, 'A parser is required'
        assert callable(decoder), 'Invalid decoder %s' % decoder
        assert isinstance(separator, str), 'Invalid separator %s' % separator
        
        self.parser = parser
        self.decoder = decoder
        self.separator = separator
        
        self.path = []
        self.content = deque()
        self.contains = deque()
        self.errors = None
        
        self.contains.append(False)

    def startElement(self, name, attributes):
        '''
        @see: ContentHandler.startElement
        '''
        if attributes:
            self.report('No attributes accepted for \'%s\' at line %s and column %s' % 
                        ('/'.join(self.path), self.parser.getLineNumber(), self.parser.getColumnNumber()))
        self.path.append(name)
        self.content.appendleft([])
        self.contains[0] = True
        self.contains.appendleft(False)

    def characters(self, content):
        '''
        @see: ContentHandler.characters
        '''
        self.content[0].append(content)

    def endElement(self, name):
        '''
        @see: ContentHandler.endElement
        '''
        if not self.path:
            self.report('Unexpected end element \'%s\' at line %s and column %s' % 
                        (name, self.parser.getLineNumber(), self.parser.getColumnNumber()))
            return
        
        if name != self.path[-1]:
            self.report('Expected end element \'%s\' at line %s and column %s, got \'%s\'' % 
                        (self.path[-1], self.parser.getLineNumber(), self.parser.getColumnNumber(), name))

        contains = self.contains.popleft()
        if contains:
            content = ''.join(self.content.popleft()).strip()
            if content:
                self.report('Invalid value \'%s\' for element \'%s\' at line %s and column %s' % 
                            (content, name, self.parser.getLineNumber(), self.parser.getColumnNumber()))
        else:
            content = '\n'.join(self.content.popleft())
            if not self.decoder(self.separator.join(self.path), content): 
                self.report('Invalid path \'%s\' at line %s and column %s' % 
                            ('/'.join(self.path), self.parser.getLineNumber(), self.parser.getColumnNumber()))
            self.path.pop()

    # ----------------------------------------------------------------
    
    def report(self, error):
        '''
        Report an error.
        '''
        assert isinstance(error, str), 'Invalid error %s' % error
        if self.errors is None: self.errors = []
        self.errors.append(error)
