'''
Created on Jun 22, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the XML encoder processor handler.
'''

from .base import RenderBaseHandler
from ally.container.ioc import injected
from ally.core.spec.transform.index import IIndexer, BLOCK, PREPARE, ADJUST, \
    AttrValue
from ally.core.spec.transform.render import IRender
from ally.support.util import immut
from ally.support.util_io import IOutputStream
from codecs import getwriter
from collections import deque
from xml.sax.saxutils import XMLGenerator, quoteattr
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

GROUP_NAME = '$name'  # The group that captures the prepared name
GROUP_ATTRIBUTES = '$attributes'  # The group that captures the prepared attributes

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

    def renderFactory(self, charSet, output, indexer):
        '''
        @see: RenderBaseHandler.renderFactory
        '''
        assert isinstance(charSet, str), 'Invalid char set %s' % charSet
        assert isinstance(output, IOutputStream), 'Invalid content output stream %s' % output

        outputb = getwriter(charSet)(output, self.encodingError)
        return RenderXML(indexer, out=outputb, encoding=charSet, short_empty_elements=True)

# --------------------------------------------------------------------

class RenderXML(XMLGenerator, IRender):
    '''
    Renderer for xml.
    '''
    
    def __init__(self, indexer, **keyargs):
        '''
        Construct the XML object renderer.
        
        @param indexer: IIndexer|None
            The indexer to push the indexes in.
        @param keyargs: key arguments
            The key arguments used for constructing the XML generator.
        '''
        assert indexer is None or isinstance(indexer, IIndexer), 'Invalid indexer %s' % indexer
        XMLGenerator.__init__(self, **keyargs)
        
        self._stack = deque()
        self._length = 0
        self._indexer = indexer

    def _write(self, text):
        '''
        @see: XMLGenerator._write
        '''
        self._length += len(text)
        super()._write(text)

    # ----------------------------------------------------------------
    
    def property(self, name, value, *index):
        '''
        @see: IRender.property
        '''
        assert isinstance(value, (str, list, dict)), 'Invalid value %s' % value
        
        block = False
        if self._indexer and index:
            for ind in index:
                assert ind == BLOCK, 'Invalid index %s' % index
                block = True
        
        self._finish_pending_start_element()
        
        if block: self._indexer.block(self._length, name)
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
        if block: self._indexer.end(self._length)

    def beginObject(self, name, attributes, *index):
        '''
        @see: IRender.beginObject
        '''
        block = prepare = adjust = False
        attrValues = None
        if self._indexer and index:
            for ind in index:
                if ind == BLOCK: block = True
                elif ind == PREPARE: prepare = True
                elif ind == ADJUST: adjust = True
                else:
                    assert isinstance(ind, AttrValue), 'Invalid index %s' % ind
                    if attrValues is None: attrValues = {}
                    attrValues[ind.attribute] = ind.name
        
        if not self._stack: self.startDocument()  # Start the document
        self._finish_pending_start_element()
        
        if block: self._indexer.block(self._length, name)
        if adjust: self._indexer.inject(0).end(self._length) 
        # For adjusting we ensure that all data is deleted until this index where the actual block starts
        self._write('<')
        start = self._length
        self._write(name)
        if prepare:
            self._indexer.group(start, GROUP_NAME).end(self._length)
            self._indexer.group(self._length, GROUP_ATTRIBUTES)
        if adjust:
            self._indexer.inject(start, GROUP_NAME).end(self._length)
            self._indexer.inject(self._length, GROUP_ATTRIBUTES).end(self._length)
        
        if attributes:
            assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
            for nameAttr, valueAttr in attributes.items():
                if attrValues and nameAttr in attrValues:
                    self._write(' %s=' % nameAttr)
                    self._indexer.group(self._length + 1, attrValues[nameAttr])  # +1 for the comma
                    self._write(quoteattr(valueAttr))
                    self._indexer.end(self._length - 1)  # -1 for the commas
                else: self._write(' %s=%s' % (nameAttr, quoteattr(valueAttr)))
        if prepare: self._indexer.end(self._length)
                
        if self._short_empty_elements:
            self._pending_start_element = True
        else:
            self._write(">")
            
        self._stack.append((name, block, adjust))
        
        return self

    def beginCollection(self, name, attributes, *index):
        '''
        @see: IRender.beginCollection
        '''
        return self.beginObject(name, attributes, *index)

    def end(self):
        '''
        @see: IRender.end
        '''
        assert self._stack, 'No object to end'
        name, block, adjust = self._stack.pop()
        
        if self._pending_start_element:
            self._write('/>')
            self._pending_start_element = False
        else:
            self._write('</')
            start = self._length
            self._write(name)
            if adjust: self._indexer.inject(start, GROUP_NAME).end(self._length)
            self._write('>')
        if block: self._indexer.end(self._length)
        if not self._stack: self.endDocument()  # Close the document if there are no other processes queued
