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
from ally.core.spec.transform.encdec import IRender
from ally.core.spec.transform.index import NAME_BLOCK, ACTION_DISCARD, \
    ACTION_STREAM, ACTION_INJECT, ACTION_NAME, Index
from ally.indexing.spec.model import Block, Action
from ally.indexing.spec.perform import skip, feed, feedValue, feedName, \
    feedIndexed, feedContent, push, pop, setFlagIfBefore, remFlag
from ally.support.util import immut
from codecs import getwriter
from collections import deque
from functools import partial
from io import BytesIO
from xml.sax.saxutils import XMLGenerator, quoteattr

# --------------------------------------------------------------------

# The patterns to use in creating XML specific names.
PATTERN_XML_BLOCK = 'XML block %s'  # The XML block pattern name.
PSIND_ATTR_CAPTURE = 'XML start capture %s'  # The pattern used for start indexes used in capturing attributes.
PEIND_ATTR_CAPTURE = 'XML end capture %s'  # The pattern used for indexes used in capturing attributes.

# The names.
NAME_XML_START_ADJUST = 'XML start adjust'
NAME_XML_END_ADJUST = 'XML end adjust'

# Variables
VAR_XML_NAME = 'XML tag name'  # The name used for the tag name.
VAR_XML_ATTRS = 'XML tag attributes'  # The name used for the tag attributes.

# The XML actions.
ACTION_XML_ADJUST = 'adjust'  # The adjust action.

# The standard XML indexes.
IND_DECL = 'XML declarations'
SIND_TAG, EIND_TAG = 'XML start tag', 'XML end tag'
SIND_CLOSE_TAG, EIND_CLOSE_TAG = 'XML start close tag', 'XML end close tag'
SIND_NAME, EIND_NAME = 'XML start tag name', 'XML end tag name'
SIND_ATTRS, EIND_ATTRS = 'XML start tag attributes', 'XML end tag attributes'
SIND_CLOSE_NAME, EIND_CLOSE_NAME = 'XML close start tag name', 'XML close end tag name'

# The JSON flags.
FLAG_TAG_CLOSED = 'close tag present'

# The escape characters for content value.
ESCAPE_XML_CONTENT = {'&': '&amp;', '>': '&gt;', '<': '&lt;'}
# The escape characters for attribute value.
ESCAPE_XML_ATTRIBUTE = {'"': "&quot;", '\n': '&#10;', '\r': '&#13;', '\t':'&#9;'}
ESCAPE_XML_ATTRIBUTE.update(ESCAPE_XML_CONTENT)

# The XML block.
BLOCK_XML = Block(
                  Action(ACTION_NAME,
                         skip(SIND_NAME), feed(EIND_NAME),
                         rewind=True, final=False),
                  Action(ACTION_STREAM,
                         skip(SIND_TAG), feed(EIND_CLOSE_TAG)),
                  Action(ACTION_DISCARD,
                         skip(EIND_CLOSE_TAG)),
                  )
                                  
# Provides the XML standard block definitions.
BLOCKS_XML = {
              NAME_XML_START_ADJUST:  
              Block(
                    Action(ACTION_XML_ADJUST,
                           skip(IND_DECL),
                           feed(SIND_NAME), skip(EIND_NAME), feedName(VAR_XML_NAME),
                           feed(EIND_ATTRS), feedName(VAR_XML_ATTRS),
                           feed(EIND_TAG)),
                    Action(ACTION_STREAM,
                           feed(EIND_TAG)),
                    ),
              
              PATTERN_XML_BLOCK % NAME_BLOCK: BLOCK_XML,
              
              NAME_XML_END_ADJUST:
              Block(
                    Action(ACTION_XML_ADJUST,
                           skip(SIND_CLOSE_TAG),
                           setFlagIfBefore(EIND_CLOSE_TAG, FLAG_TAG_CLOSED),
                           feed(SIND_CLOSE_NAME), skip(EIND_CLOSE_NAME), feedName(VAR_XML_NAME, FLAG_TAG_CLOSED),
                           feed(EIND_CLOSE_TAG), remFlag(FLAG_TAG_CLOSED)),
                    Action(ACTION_STREAM,
                           skip(SIND_CLOSE_TAG),
                           feed(EIND_CLOSE_TAG)),
                    ),
              }

def createXMLAttributesActions(injectAttributes=None, captureAttributes=None):
    '''
    Create the actions associated with the provided attributes.
    
    @param injectAttributes: dictionary{string: string}
        The attributes to be injected dictionary, as a key the action to be associated with the attribute injection and
        as a value the attribute name to be injected.
    @param captureAttributes: dictionary{string: string}
        The attributes to be captured dictionary, as a key the action to be associated with the attribute capture and
        as a value the name to be used latter on as a reference for the attribute capture.
    @return: list[Action]
        The created list of actions for the attributes.
    '''
    actions = []
    if injectAttributes:
        assert isinstance(injectAttributes, dict), 'Invalid inject attributes %s' % injectAttributes
        for action, nameAttr in injectAttributes.items():
            actions.append(Action(action,
                                  skip(SIND_TAG), feed(EIND_ATTRS),
                                  feedValue(' %s="' % nameAttr), feedContent(escapes=ESCAPE_XML_ATTRIBUTE), feedValue('"'),
                                  final=False))
    
    if captureAttributes:
        assert isinstance(captureAttributes, dict), 'Invalid capture attributes %s' % captureAttributes
        for action, name in captureAttributes.items():
            actions.append(Action(action,
                                  skip(PSIND_ATTR_CAPTURE % name),
                                  feed(PEIND_ATTR_CAPTURE % name),
                                  rewind=True, final=False))
    return actions

def createXMLBlockForIndexed(name, *actions, injectAttributes=None, captureAttributes=None):
    '''
    Create a new XML block that can be used for injecting indexed content.
    
    @param name: string
        The name that can be latter on used as a reference for the block.
    @param actions: arguments[Action]
        Additional actions to be registered with the created block.
    @see: createXMLAttributesActions
    '''
    actions = list(actions)
    actions.extend(BLOCK_XML.actions)
    actions.extend(createXMLAttributesActions(injectAttributes, captureAttributes))
    actions.append(Action(ACTION_INJECT,
                          skip(SIND_NAME), push(VAR_XML_NAME, EIND_NAME),
                          skip(SIND_ATTRS), push(VAR_XML_ATTRS, EIND_ATTRS),
                          skip(EIND_CLOSE_TAG),
                          feedIndexed(actions=(ACTION_XML_ADJUST,)),
                          pop(VAR_XML_NAME), pop(VAR_XML_ATTRS),
                          ))
    return {PATTERN_XML_BLOCK % name: Block(*actions)}
    
def createXMLBlockForContent(name, *actions, injectAttributes=None, captureAttributes=None):
    '''
    Create a new XML block that can be used for injecting text content.
    
    @param name: string
        The name that can be latter on used as a reference for the block.
    @param actions: arguments[Action]
        Additional actions to be registered with the created block.
    @see: createXMLAttributesActions
    '''
    actions = list(actions)
    actions.extend(BLOCK_XML.actions)
    actions.extend(createXMLAttributesActions(injectAttributes, captureAttributes))
    actions.append(Action(ACTION_INJECT,
                          skip(SIND_NAME), push(VAR_XML_NAME, EIND_NAME),
                          skip(SIND_ATTRS), push(VAR_XML_ATTRS, EIND_ATTRS),
                          skip(EIND_CLOSE_TAG),
                          feedValue('<'), feedName(VAR_XML_NAME), feedName(VAR_XML_ATTRS), feedValue('>'),
                          feedContent(escapes=ESCAPE_XML_CONTENT),
                          feedValue('</'), feedName(VAR_XML_NAME), feedValue('>'),
                          pop(VAR_XML_NAME), pop(VAR_XML_ATTRS),
                          ))
    
    return {PATTERN_XML_BLOCK % name: Block(*actions)}

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
        self._block = False
        self._pendingStart = None
        self._indexes = []

    # ----------------------------------------------------------------
    
    def property(self, name, value, indexBlock=None):
        '''
        @see: IRender.property
        
        @param indexBlock: string
            Index the object with the provided index.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(value, (str, list, dict)), 'Invalid value %s' % value
        if indexBlock is None and not self._block: indexBlock = NAME_BLOCK
        
        self.begin(name, indexBlock=indexBlock)
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
        self.end()

    def beginObject(self, name, **specifications):
        '''
        @see: IRender.beginObject
        '''
        self.begin(name, **specifications)
        return self

    def beginCollection(self, name, **specifications):
        '''
        @see: IRender.beginCollection
        
        @see: beginObject
        '''
        self.begin(name, **specifications)
        return self

    def end(self):
        '''
        @see: IRender.end
        '''
        assert self._stack, 'No object to end'
        name, index, isAdjust = self._stack.pop()
        
        if isAdjust: index = self._index(NAME_XML_END_ADJUST)
        if self._pending_start_element:
            self._write('/>')
            if self._pendingStart: self._pendingStart(EIND_TAG)
            if index: index(SIND_CLOSE_TAG, SIND_CLOSE_NAME, EIND_CLOSE_NAME, EIND_CLOSE_TAG)
            self._pending_start_element = False
            self._pendingStart = None
        else:
            if index: index(SIND_CLOSE_TAG)
            self._write('</')
            if index: index(SIND_CLOSE_NAME)
            self._write(name)
            if index: index(EIND_CLOSE_NAME)
            self._write('>')
            if index: index(EIND_CLOSE_TAG)
        if index: self._block = False
        
        if not self._stack:
            self.endDocument()  # Close the document if there are no other processes queued
            content = self._content
            assert isinstance(content, Content), 'Invalid content %s' % content
            content.length = self._outb.tell()
            self._outb.seek(0)
            content.source = self._outb
            content.indexes = self._indexes
        
    # ----------------------------------------------------------------
    
    def begin(self, name, attributes=None, indexBlock=None, indexAttributesCapture=immut()):
        '''
        Begins a XML tag.
        
        @param attributes: dictionary{string: string}
            The attributes to associate with the object.
        @param indexBlock: string
            Index the object with the provided index.
        @param indexAttributesCapture: dictionary{string: string}
            The dictionary containing as a key the attribute name and as a value the key name as registered
            to associate with the attribute capture.
        '''
        isAdjust = False
        if self._adjust:
            self.startDocument()  # Start the document
            if indexBlock is None:
                assert indexBlock is None, 'No index block expected, but got %s' % indexBlock
                assert not indexAttributesCapture, 'No attributes capture expected, but got %s' % indexAttributesCapture
                index = self._index(NAME_XML_START_ADJUST)
                index(IND_DECL)
                isAdjust = True
            self._adjust = False
        if not isAdjust:
            if self._block:
                assert indexBlock is None, 'No index block expected, but got %s' % indexBlock
                assert not indexAttributesCapture, 'No attributes capture expected, but got %s' % indexAttributesCapture
                index = None
            elif indexBlock:
                assert isinstance(indexBlock, str), 'Invalid index block %s' % indexBlock
                assert isinstance(indexAttributesCapture, dict), 'Invalid index attributes capture %s' % indexAttributesCapture
                index = self._index(PATTERN_XML_BLOCK % indexBlock)
                self._block = True
            else: index = None
        
        if self._pending_start_element:
            self._write('>')
            if self._pendingStart: self._pendingStart(EIND_TAG)
            self._pending_start_element = False
            self._pendingStart = None
        
        if index: index(SIND_TAG)
        self._write('<')
        if index: index(SIND_NAME)
        self._write(name)
        if index: index(EIND_NAME)
        
        if index: index(SIND_ATTRS)
        if attributes:
            assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
            for nameAttr, valueAttr in attributes.items():
                assert isinstance(nameAttr, str), 'Invalid attribute name %s' % nameAttr
                assert isinstance(valueAttr, str), 'Invalid attribute value %s' % valueAttr
                
                iname = indexAttributesCapture.get(nameAttr)
                if iname:
                    self._write(' %s=' % nameAttr)
                    index(PSIND_ATTR_CAPTURE % iname, offset=1)  # offset +1 for the comma
                    self._write(quoteattr(valueAttr))
                    index(PEIND_ATTR_CAPTURE % iname, offset= -1)  # offset -1 for the comma
                else: self._write(' %s=%s' % (nameAttr, quoteattr(valueAttr)))
        if index: index(EIND_ATTRS)
                
        if self._short_empty_elements:
            self._pending_start_element = True
            self._pendingStart = index
        else:
            self._write('>')
            if index: index(EIND_TAG)
            
        self._stack.append((name, index, isAdjust))
        return self
    
    def _index(self, block):
        '''
        Create a new index.
        '''
        index = Index(block)
        self._indexes.append(index)
        return partial(self._put, index)
    
    def _put(self, index, *names, offset=0):
        '''
        Puts on the index the provided index names at the current offset. 
        '''
        assert isinstance(index, Index), 'Invalid index %s' % index
        offset = self._outb.tell() + offset
        for name in names:
            assert isinstance(name, str), 'Invalid name %s' % name
            index.values[name] = offset
