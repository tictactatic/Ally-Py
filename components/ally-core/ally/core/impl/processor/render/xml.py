'''
Created on Jun 22, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the XML encoder processor handler.
'''

from .base import RenderBaseHandler, PatternBaseHandler
from ally.container.ioc import injected
from ally.core.spec.transform.flags import DYNAMIC_NAME
from ally.core.spec.transform.render import IRender
from ally.core.spec.transform.representation import Object, Property, Attribute
from ally.support.util import immut
from ally.support.util_io import IOutputStream
from codecs import getwriter
from collections import deque
from xml.sax.saxutils import XMLGenerator
import logging
import re

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@injected
class RenderXMLHandler(RenderBaseHandler):
    '''
    Provides the XML rendering.
    @see: RenderBaseHandler
    '''

    encodingError = 'xmlcharrefreplace'
    # The encoding error resolving.

    def __init__(self):
        assert isinstance(self.encodingError, str), 'Invalid string %s' % self.encodingError
        super().__init__()

    def renderFactory(self, charSet, output):
        '''
        @see: RenderBaseHandler.renderFactory
        '''
        assert isinstance(charSet, str), 'Invalid char set %s' % charSet
        assert isinstance(output, IOutputStream), 'Invalid content output stream %s' % output

        outputb = getwriter(charSet)(output, self.encodingError)
        xml = XMLGenerator(outputb, charSet, short_empty_elements=True)
        return RenderXML(xml)

# --------------------------------------------------------------------

class PatternXMLHandler(PatternBaseHandler):
    '''
    Provides the XML pattern.
    @see: PatternBaseHandler
    '''
    
    identifier = 'xml'
    # The identifier for the represented pattern.
    adjusters = (('^\s*<\?.*\?>\s*<\w+', '<{1}{2}'), ('</\w+\s*>\s*$', '</{1}>'))
    # The injector adjusters.
    
    def matcher(self, obj, injected):
        '''
        @see: IPattern.matcher
        '''
        assert isinstance(injected, bool), 'Invalid injected flag %s' % injected
        
        if isinstance(obj, (Property, Object)):
            assert isinstance(obj, (Property, Object))
            if DYNAMIC_NAME in obj.flags: raise ValueError('Cannot provide matcher for a dynamic named object %s' % obj)
            name = re.escape(obj.name)
            if injected: return '(?s)<(%s)((?:\s+[^>]*)*)(?:(?:/>)|(?:>.*?</%s>))' % (name, name)
            return '(?s)<%s(?:\s+[^>]*)*(?:(?:/>)|(?:>.*?</%s>))' % (name, name)
            
        raise ValueError('Cannot create a matcher for object %s' % obj)
            
    def capture(self, obj):
        '''
        @see: IPattern.capture
        '''
        if isinstance(obj, Attribute):
            assert isinstance(obj, Attribute)
            return '%s\s*\=\s*(?:"([^"]+)"|\'([^\']+)\')*' % obj.name
        raise ValueError('Cannot create a capture for object %s' % obj)
    
    def injector(self, obj):
        '''
        @see: IPattern.injector
        '''
        if isinstance(obj, Attribute):
            assert isinstance(obj, Attribute)
            return ('(^\s*<.+?)((?:>)|(?:/>)){1}', '\\1 %s="*"\\2' % obj.name)
        raise ValueError('Cannot create a injector for object %s' % obj)
        
# --------------------------------------------------------------------

class RenderXML(IRender):
    '''
    Renderer for xml.
    '''
    __slots__ = ('xml', 'stack')

    def __init__(self, xml):
        '''
        Construct the XML object renderer.
        
        @param xml: XMLGenerator
            The xml generator used to render the xml.
        '''
        assert isinstance(xml, XMLGenerator), 'Invalid xml generator %s' % xml

        self.xml = xml
        self.stack = deque()

    def property(self, name, value):
        '''
        @see: IRender.property
        '''
        assert isinstance(value, (str, list, dict)), 'Invalid value %s' % value

        self.xml.startElement(name, immut())
        if isinstance(value, list):
            for item in value:
                assert isinstance(item, str), 'Invalid list item %s' % item
                self.xml.startElement('value', immut())
                self.xml.characters(item)
                self.xml.endElement('value')
        elif isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(key, str), 'Invalid dictionary key %s' % key
                assert isinstance(item, str), 'Invalid dictionary value %s' % item
                self.xml.startElement('entry', immut())
                self.xml.startElement('key', immut())
                self.xml.characters(key)
                self.xml.endElement('key')
                self.xml.startElement('value', immut())
                self.xml.characters(item)
                self.xml.endElement('value')
                self.xml.endElement('entry')
        else:
            self.xml.characters(value)
        self.xml.endElement(name)

    def beginObject(self, name, attributes=None):
        '''
        @see: IRender.beginObject
        '''
        if not self.stack: self.xml.startDocument()  # Start the document
        self.stack.append(name)
        self.xml.startElement(name, attributes or immut())
        
        return self

    def beginCollection(self, name, attributes=None):
        '''
        @see: IRender.beginCollection
        '''
        if not self.stack: self.xml.startDocument()  # Start the document
        self.stack.append(name)
        self.xml.startElement(name, attributes or immut())
        
        return self

    def end(self):
        '''
        @see: IRender.end
        '''
        assert self.stack, 'No object to end'

        self.xml.endElement(self.stack.pop())
        if not self.stack: self.xml.endDocument()  # Close the document if there are no other processes queued
