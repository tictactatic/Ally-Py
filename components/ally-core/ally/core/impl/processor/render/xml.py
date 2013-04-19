'''
Created on Jun 22, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the XML encoder processor handler.
'''

from .base import Content, RenderBaseHandler
from ally.container.ioc import injected
from ally.core.spec.transform.index import GROUP_PREPARE, ACTION_CAPTURE, \
    GROUP_ADJUST, ACTION_INJECT, NAME_BLOCK, NAME_ADJUST, PLACE_HOLDER
from ally.core.spec.transform.render import IRender
from ally.support.util import immut
from codecs import getwriter
from collections import deque
from io import BytesIO
from xml.sax.saxutils import XMLGenerator, quoteattr

# --------------------------------------------------------------------

XML_PREPARE_NAME = 'XML prepare tag name'  # The XML tag name prepare
XML_PREPARE_ATTRIBUTES = 'XML prepare attributes'  # The XML attributes prepare
XML_ADJUST_NAME = 'XML adjust tag name'  # The XML tag name adjust
XML_ADJUST_ATTRIBUTES = 'XML adjust attributes'  # The XML attributes adjust

XML_CONTENT_INJECT_PATTERN = 'XML inject content %s'  # The pattern used in creating the injected content.
# The escape characters for content value.
XML_CONTENT_ESCAPE = '[\&\>\<]'
XML_CONTENT_ESCAPE_DICT = {'&': '&amp;', '>': '&gt;', '<': '&lt;'}

XML_ATTRIBUTE_INJECT_PATTERN = 'XML inject attribute %s'  # The pattern used in creating the injected attributes.
# The escape characters for attribute value.
XML_ATTRIBUTE_ESCAPE = '%s\"\n\r\t]' % XML_CONTENT_ESCAPE[:-1]
XML_ATTRIBUTE_ESCAPE_DICT = {'"': "&quot;", '\n': '&#10;', '\r': '&#13;', '\t':'&#9;'}
XML_ATTRIBUTE_ESCAPE_DICT.update(XML_CONTENT_ESCAPE_DICT)

# --------------------------------------------------------------------

# Provides the XML markers definitions.
XML_MARKERS = {
               XML_PREPARE_NAME: immut(group=GROUP_PREPARE, action=ACTION_CAPTURE),
               XML_PREPARE_ATTRIBUTES: immut(group=GROUP_PREPARE, action=ACTION_CAPTURE),
               XML_ADJUST_NAME: immut(group=GROUP_ADJUST, action=ACTION_INJECT, source=XML_PREPARE_NAME),
               XML_ADJUST_ATTRIBUTES: immut(group=GROUP_ADJUST, action=ACTION_INJECT, source=XML_PREPARE_ATTRIBUTES),
               }

def createXMLContentInjectMarker(group, value):
    '''
    Provides the the XML marker definitions for injecting content.
    
    @param group: string
        The group of the content inject marker.
    @param value: string
        The value of the content inject marker.
    '''
    assert isinstance(group, str), 'Invalid group %s' % group
    assert isinstance(value, str), 'Invalid group %s' % value
    
    definitions = {}
    definition = definitions[XML_CONTENT_INJECT_PATTERN % group] = {}
    definition['group'] = group
    definition['action'] = ACTION_INJECT
    # We need to recreate the XML tags that will contain the content.
    definition['values'] = ['<', PLACE_HOLDER % XML_PREPARE_NAME, PLACE_HOLDER % XML_PREPARE_ATTRIBUTES, '>', value,
                            '</', PLACE_HOLDER % XML_PREPARE_NAME, '>']
    definition['replace'] = XML_CONTENT_ESCAPE
    definition['replaceMapping'] = XML_CONTENT_ESCAPE_DICT
        
    return definitions

def createXMLAttrsInjectMarkers(group, attributes):
    '''
    Provides the the XML markers definitions for injecting attributes, the attributes names are declared as marker targets.
    
    @param group: string
        The group of the attributes inject markers.
    @param attributes: dictionary{string: string}
        The attributes to be injected, a dictionary containing on the first position the attribute name
        and as a value the attribute value to be injected.
    @return: dictionary{string: ...}
        The inject attributes definitions.
    '''
    assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
    assert attributes, 'At least an attribute name is required'
    assert isinstance(group, str), 'Invalid group %s' % group
    
    definitions = {}
    for name, value in attributes.items():
        assert isinstance(name, str), 'Invalid attribute name %s' % name
        assert isinstance(value, str), 'Invalid attribute value %s' % value
        
        definition = definitions[XML_ATTRIBUTE_INJECT_PATTERN % name] = {}
        definition['group'] = group
        definition['action'] = ACTION_INJECT
        definition['target'] = name
        definition['values'] = [' %s="' % name, value, '"']
        
        definition['replace'] = XML_ATTRIBUTE_ESCAPE
        definition['replaceMapping'] = XML_ATTRIBUTE_ESCAPE_DICT
        
    return definitions

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

    def renderFactory(self, content):
        '''
        @see: RenderBaseHandler.renderFactory
        '''
        return RenderXML(self.encodingError, content)

# --------------------------------------------------------------------

class RenderXML(XMLGenerator, IRender):
    '''
    Renderer for XML.
    '''
    
    def __init__(self, encodingError, content):
        '''
        Construct the XML object renderer.
        
        @param encodingError: string
            The encoding error resolving.
        @param content: Content
            The content to render in.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(content.charSet, str), 'Invalid content char set %s' % content.charSet
        
        self._outb = BytesIO()
        XMLGenerator.__init__(self, out=getwriter(content.charSet)(self._outb, encodingError),
                              encoding=content.charSet, short_empty_elements=True)
        
        self._content = content
        
        self._stack = deque()
        self._adjust = True
        self._block = True
        self._indexes = []

    # ----------------------------------------------------------------
    
    def property(self, name, value, indexBlock=False):
        '''
        @see: IRender.property
        '''
        assert isinstance(value, (str, list, dict)), 'Invalid value %s' % value
        assert isinstance(indexBlock, bool), 'Invalid index block flag %s' % indexBlock
        indexBlock = self._block and indexBlock
        
        self._finish_pending_start_element()
        
        if indexBlock: self._indexStart(NAME_BLOCK, name)
        self.startElement(name, immut())
        if isinstance(value, list):
            for item in value:
                assert isinstance(item, str), 'Invalid list item %s' % item
                self.startElement('value', immut())
                self.characters(item)
                self.endElement('value')
        elif isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(key, str), 'Invalid dictionary key %s' % key
                assert isinstance(item, str), 'Invalid dictionary value %s' % item
                self.startElement('entry', immut())
                self.startElement('key', immut())
                self.characters(key)
                self.endElement('key')
                self.startElement('value', immut())
                self.characters(item)
                self.endElement('value')
                self.endElement('entry')
        else:
            self.characters(value)
        self.endElement(name)
        if indexBlock: self._indexEnd()

    def beginObject(self, name, attributes=None, indexBlock=False, indexPrepare=False, indexContentInject=(),
                    indexAttributesInject=(), indexAttributesCapture=immut()):
        '''
        @see: IRender.beginObject
        
        @param attributes: dictionary{string: string}
            The attributes to associate with the object.
        @param indexBlock: boolean
            Flag indicating that a block index should be created for the object.
        @param indexPrepare: boolean
            Flag indicating that the object should be prepared to be injected with another REST content.
        @param indexContentInject: list[string]|tuple(string)
            The list or tuple containing the group names (previously registered with @see: createXMLContentInjectMarkers)
            to be injected instead of object block.
        @param indexAttributesInject: list[string]|tuple(string)
            The list or tuple containing the attribute names (previously registered with @see: createXMLAttrsInjectMarkers)
            to be injected.
        @param indexAttributesCapture: dictionary{string: string}
            The dictionary containing as a key the attribute name and as a value the marker to associate with the attribute
            capture.
        '''
        assert isinstance(indexBlock, bool), 'Invalid index block flag %s' % indexBlock
        assert isinstance(indexPrepare, bool), 'Invalid index prepare flag %s' % indexPrepare
        assert isinstance(indexContentInject, (tuple, list)), 'Invalid index content inject %s' % indexContentInject
        assert isinstance(indexAttributesInject, (tuple, list)), 'Invalid index attributes inject %s' % indexAttributesInject
        assert isinstance(indexAttributesCapture, dict), 'Invalid index attributes capture %s' % indexAttributesCapture
        
        indexAdjust, indexBlock = self._adjust, self._block and indexBlock and not self._adjust
        indexPrepare = indexBlock and indexPrepare
        self._adjust = False
        
        if indexAdjust: self._indexStart(NAME_ADJUST)
        if not self._stack: self.startDocument()  # Start the document
        self._finish_pending_start_element()
        if indexAdjust: self._indexEnd()
        
        if indexBlock: self._indexStart(NAME_BLOCK, name)
        for group in indexContentInject: self._indexStart(XML_CONTENT_INJECT_PATTERN % group)
        
        self._write('<')
        if indexAdjust: self._indexStart(XML_ADJUST_NAME)
        if indexPrepare: self._indexStart(XML_PREPARE_NAME)
        self._write(name)
        if indexPrepare: self._indexEnd()
        if indexAdjust: self._indexEnd()
        
        if indexAdjust:self._indexAt(XML_ADJUST_ATTRIBUTES)
        
        if attributes:
            if indexPrepare: self._indexStart(XML_PREPARE_ATTRIBUTES)
            assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
            for nameAttr, valueAttr in attributes.items():
                if nameAttr in indexAttributesCapture:
                    self._write(' %s=' % nameAttr)
                    self._indexStart(indexAttributesCapture[nameAttr], offset=1)  # offset +1 for the comma
                    self._write(quoteattr(valueAttr))
                    self._indexEnd(offset= -1)  # offset -1 for the comma
                else: self._write(' %s=%s' % (nameAttr, quoteattr(valueAttr)))
            if indexPrepare: self._indexEnd()
            
        for attr in indexAttributesInject: self._indexAt(XML_ATTRIBUTE_INJECT_PATTERN % attr)
                
        if self._short_empty_elements:
            self._pending_start_element = True
        else:
            self._write('>')
            
        self._stack.append((name, indexAdjust, indexBlock, indexContentInject))
        return self

    def beginCollection(self, name, **specifications):
        '''
        @see: IRender.beginCollection
        
        @see: beginObject
        '''
        return self.beginObject(name, **specifications)

    def end(self):
        '''
        @see: IRender.end
        '''
        assert self._stack, 'No object to end'
        name, indexAdjust, indexBlock, indexContentInject = self._stack.pop()
        
        if self._pending_start_element:
            self._write('/>')
            self._pending_start_element = False
        else:
            self._write('</')
            if indexAdjust: self._indexStart(XML_ADJUST_NAME)
            self._write(name)
            if indexAdjust: self._indexEnd()
            self._write('>')
        for _group in indexContentInject: self._indexEnd()
        if indexBlock:
            self._indexEnd()
            self._block = True
        
        if not self._stack:
            self.endDocument()  # Close the document if there are no other processes queued
            content = self._content
            assert isinstance(content, Content), 'Invalid content %s' % content
            content.length = self._outb.tell()
            self._outb.seek(0)
            content.source = self._outb
            content.indexes = self._indexes
        
    # ----------------------------------------------------------------
    
    def _indexAt(self, marker, value=None, offset=0):
        '''
        Creates an index that starts and ends at the current offset.
        '''
        at = self._outb.tell() + offset
        self._indexes.append((at, (marker, value)))
        self._indexes.append((at, None))
        
    def _indexStart(self, marker, value=None, offset=0):
        '''
        Starts and index at the current offset.
        '''
        self._indexes.append((self._outb.tell() + offset, (marker, value)))
        
    def _indexEnd(self, offset=0):
        '''
        Ends the ongoing index at the current offset.
        '''
        self._indexes.append((self._outb.tell() + offset, None))
