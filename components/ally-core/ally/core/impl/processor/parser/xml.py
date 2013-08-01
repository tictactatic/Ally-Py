'''
Created on Aug 24, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the XML parser processor handler.
'''

from . import base
from .base import ParseBaseHandler, Target
from ally.container.ioc import injected
from ally.core.impl.processor.base import addFailure
from ally.design.processor.attribute import requires, optional
from ally.support.util_io import IInputStream
from ally.support.util_spec import IDo
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
    # ---------------------------------------------------------------- Optional
    isMandatory = optional(bool)
    # ---------------------------------------------------------------- Required
    name = requires(str)
    children = requires(dict)
    doBegin = requires(IDo)
    doDecode = requires(IDo)
    doEnd = requires(IDo)
    
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

    def parse(self, source, charSet, decoding, target):
        '''
        @see: ParseBaseHandler.parse
        '''
        assert isinstance(source, IInputStream), 'Invalid stream %s' % source
        assert isinstance(charSet, str), 'Invalid character set %s' % charSet
        assert isinstance(target, Target), 'Invalid target %s' % target
        
        parse = Parse(self.parser, decoding, target)
        self.parser.setContentHandler(parse)
        inpsrc = InputSource()
        inpsrc.setByteStream(source)
        inpsrc.setEncoding(charSet)
        try: self.parser.parse(source)
        except SAXParseException as e:
            assert isinstance(e, SAXParseException)
            addFailure(target, decoding, 'Bad XML content at line %(line)s and column %(column)s',
                       line=e.getLineNumber(), column=e.getColumnNumber())

# --------------------------------------------------------------------

class Parse(ContentHandler):
    '''
    Content handler used for parsing the xml content.
    '''
    __slots__ = ('parser', 'decoding', 'target', 'last', 'isInvalid', 'path', 'content', 'contains', 'visited')

    def __init__(self, parser, decoding, target):
        '''
        Construct the parser.
        
        @param parser: object
            The XML parser.
        @param decoding: Decoding
            The decoding used in the parsing process.
        @param target: Target
            The target used in the parsing process.
        '''
        assert parser is not None, 'A parser is required'
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(target, Target), 'Invalid target %s' % target
        super().__init__()
        
        self.parser = parser
        self.decoding = decoding
        self.target = target

        self.last = decoding
        self.isInvalid = False
        self.path = []
        self.content = []
        self.contains = [False]
        self.visited = [set()]

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
                if Decoding.doBegin in self.last and self.last.doBegin: self.last.doBegin(self.target)
        else:
            isUnexpected = name != self.last.name
            if isUnexpected:
                self.isInvalid = True
                self.path.append(name)
            else:
                self.path.append(self.last)
                if Decoding.doBegin in self.last and self.last.doBegin: self.last.doBegin(self.target)
            
        if isUnexpected:
            addFailure(self.target, self.last, 'Unexpected element \'%(path)s\' at line %(line)s and column %(column)s',
                       **self.located(path=asPath(self.path)))
        elif attributes:
            addFailure(self.target, self.last, 'No attributes accepted for \'%(path)s\' at line %(line)s and column %(column)s',
                       **self.located(path=asPath(self.path)))

        if self.isInvalid: return
            
        self.content.append([])
        self.contains[-1] = True
        self.contains.append(False)
        self.visited[-1].add(name)
        self.visited.append(set())

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
            addFailure(self.target, self.last,
                       'Unexpected end element \'%(name)s\' at line %(line)s and column %(column)s',
                       **self.located(name=name))
            return
        
        current = self.path.pop()
        previous = self.path[-1] if self.path else self.decoding
        if self.isInvalid:
            if self.last == previous: self.isInvalid = False
            return
        
        assert isinstance(current, Decoding), 'Invalid decoding %s' % current
        self.last = previous
        visited, contains, content = self.visited.pop(), self.contains.pop(), '\n'.join(self.content.pop())
        
        abort = False
        if current.children:
            for cname, child in current.children.items():
                assert isinstance(child, Decoding), 'Invalid decoding %s' % child
                if cname not in visited and Decoding.isMandatory in child and child.isMandatory:
                    addFailure(self.target, current,
                               'Expected a value for element \'%(path)s\' at line %(line)s and column %(column)s',
                               **self.located(path=asPath(self.path, name, cname)))
                    abort = True
        
        if not abort:
            if contains or not current.doDecode:
                if content.strip():
                    addFailure(self.target, current, 'Unexpected value \'%(content)s\' for element \'%(path)s\' at '
                               'line %(line)s and column %(column)s',
                               **self.located(content=content, path=asPath(self.path, name)))
            elif content.strip(): current.doDecode(self.target, content)
            else: addFailure(self.target, current,
                             'Expected a value for element \'%(path)s\' at line %(line)s and column %(column)s',
                             **self.located(path=asPath(self.path, name)))
            
            if Decoding.doEnd in current and current.doEnd: current.doEnd(self.target)

    # ----------------------------------------------------------------
    
    def located(self, **data):
        '''
        Provides a dictionary with the line and column at the end of the provided arguments
        '''
        data['line'] = self.parser.getLineNumber()
        data['column'] = self.parser.getColumnNumber()
        return data
    
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
