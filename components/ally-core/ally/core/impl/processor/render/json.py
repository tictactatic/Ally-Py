'''
Created on Aug 3, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the JSON encoder processor handler.
'''

from .base import RenderBaseHandler, Content
from ally.container.ioc import injected
from ally.core.spec.transform.index import NAME_BLOCK, GROUP_PREPARE, \
    ACTION_CAPTURE, GROUP_ADJUST, ACTION_INJECT, PLACE_HOLDER, PLACE_HOLDER_CONTENT, \
    Index, GROUP_BLOCK_JOIN, GROUP_BLOCK_ADJUST
from ally.core.spec.transform.render import IRender
from ally.support.util import immut
from codecs import getwriter
from collections import deque
from io import BytesIO
from json.encoder import encode_basestring

# --------------------------------------------------------------------

JSON_BLOCK_JOIN = 'JSON block join'  # The JSON name for block join
JSON_BLOCK_ADJUST = 'JSON block adjust'  # The JSON name for block adjust
JSON_PREPARE_PROPERTY = 'JSON prepare property'  # The JSON property prepare
JSON_PREPARE_NAME = 'JSON prepare name'  # The JSON name prepare
JSON_PREPARE_NAME_FIXED = 'JSON prepare name fixed'  # The JSON fixed name prepare
JSON_PREPARE_ATTRIBUTES = 'JSON prepare attributes'  # The JSON attributes prepare
JSON_ADJUST_PROPERTY = 'JSON adjust property'  # The JSON property adjust
JSON_ADJUST_NAME = 'JSON adjust name'  # The JSON name adjust
JSON_ADJUST_ATTRIBUTES = 'JSON adjust attributes'  # The JSON attributes adjust

# --------------------------------------------------------------------

# Provides the JSON markers definitions.
JSON_MARKERS = {
                JSON_BLOCK_JOIN: dict(group=GROUP_BLOCK_JOIN, action=ACTION_INJECT, values=[',']),
                JSON_BLOCK_ADJUST: dict(group=GROUP_BLOCK_ADJUST, action=ACTION_INJECT),
                JSON_PREPARE_PROPERTY: dict(group=GROUP_PREPARE, action=ACTION_CAPTURE),
                JSON_PREPARE_NAME: dict(group=GROUP_PREPARE, action=ACTION_CAPTURE),
                JSON_PREPARE_NAME_FIXED: dict(group=GROUP_PREPARE),
                JSON_PREPARE_ATTRIBUTES: dict(group=GROUP_PREPARE, action=ACTION_CAPTURE,
                                               values=[PLACE_HOLDER_CONTENT, ',']),
                JSON_ADJUST_PROPERTY: dict(group=GROUP_ADJUST, action=ACTION_INJECT, source=JSON_PREPARE_PROPERTY),
                JSON_ADJUST_NAME: dict(group=GROUP_ADJUST, action=ACTION_INJECT,
                                       values=[PLACE_HOLDER % JSON_PREPARE_NAME, PLACE_HOLDER % JSON_PREPARE_NAME_FIXED]),
                JSON_ADJUST_ATTRIBUTES: dict(group=GROUP_ADJUST, action=ACTION_INJECT, source=JSON_PREPARE_ATTRIBUTES),
               }

# --------------------------------------------------------------------

@injected
class RenderJSONHandler(RenderBaseHandler):
    '''
    Provides the JSON rendering.
    @see: RenderBaseHandler
    '''

    encodingError = 'backslashreplace'
    # The encoding error resolving.

    def __init__(self):
        assert isinstance(self.encodingError, str), 'Invalid string %s' % self.encodingError
        super().__init__()

    def renderFactory(self, content):
        '''
        @see: RenderBaseHandler.renderFactory
        '''
        return RenderJSON(self.encodingError, content)

# --------------------------------------------------------------------

class RenderJSON(IRender):
    '''
    Renderer for JSON.
    '''
    __slots__ = ('_content', '_outb', '_out', '_stack', '_first', '_adjust', '_block', '_indexes')
    
    def __init__(self, encodingError, content):
        '''
        Construct the JSON object renderer.
        
        @param encodingError: string
            The encoding error resolving.
        @param content: Content
            The content to render in.
        '''
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(content.charSet, str), 'Invalid content char set %s' % content.charSet
        
        self._content = content
        self._outb = BytesIO()
        self._out = getwriter(content.charSet)(self._outb, encodingError)
        
        self._stack = deque()
        self._first = True
        
        self._adjust = True
        self._block = False
        self._indexes = []

    def property(self, name, value, indexBlock=False):
        '''
        @see: IRender.property
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(value, (str, list, dict)), 'Invalid value %s' % value
        assert isinstance(indexBlock, bool), 'Invalid index block flag %s' % indexBlock
        assert self._stack and self._stack[0][0], 'No object for property'

        if not self._first:
            if self._block or indexBlock: ablock = self._start(JSON_BLOCK_ADJUST)
            self._out.write(',')
            if self._block or indexBlock:
                self._end(ablock)
                self._block = indexBlock
        else: self._block = indexBlock
        self._first = False
        
        if indexBlock: iblock = self._start(NAME_BLOCK, name)
        self._out.write('"%s"' % name)
        self._out.write(':')
        if isinstance(value, list): value = '[%s]' % ','.join(encode_basestring(item) for item in value)
        elif isinstance(value, dict):
            value = ','.join('%s:%s' % (encode_basestring(key), encode_basestring(item)) for key, item in value.items())
            value = '{%s}' % value
        else:
            value = encode_basestring(value)
        self._out.write(value)
        if indexBlock: self._end(iblock)

    def beginObject(self, name, **specifications):
        '''
        @see: IRender.beginObject
        '''
        self.openObject(name, True, **specifications)
        return self

    def beginCollection(self, name, **specifications):
        '''
        @see: IRender.beginCollection
        '''
        self.openObject(name, False, **specifications)
        return self

    def end(self):
        '''
        @see: IRender.collectionEnd
        '''
        assert self._stack, 'No collection to end'
        isObj, iblock = self._stack.popleft()
        if not isObj: self._out.write(']')
        self._out.write('}')
        if iblock:
            self._end(iblock)
            self._block = True
        else: self._block = False
        
        if not self._stack:
            content = self._content
            assert isinstance(content, Content), 'Invalid content %s' % content
            content.length = self._outb.tell()
            self._outb.seek(0)
            content.source = self._outb
            content.indexes = self._indexes
        
    # ----------------------------------------------------------------

    def openObject(self, name, isObject, attributes=None, indexBlock=False, indexPrepare=False,
                   indexAttributesCapture=immut(), **specifications):
        '''
        Used to open a JSON object.
        
        @param attributes: dictionary{string: string}
            The attributes to associate with the object.
        @param indexBlock: boolean
            Flag indicating that a block index should be created for the object.
        @param indexPrepare: boolean
            Flag indicating that the object should be prepared to be injected with another REST content.
        @param indexContentInject: list[string]|tuple(string)
            The list or tuple containing the group names (previously registered with @see: createJSONContentInjectMarkers)
            to be injected instead of object block.
        @param indexAttributesInject: list[string]|tuple(string)
            The list or tuple containing the attribute names (previously registered with @see: createJSONAttrsInjectMarkers)
            to be injected.
        @param indexAttributesCapture: dictionary{string: string}
            The dictionary containing as a key the attribute name and as a value the marker to associate with the attribute
            capture.
        '''
        assert isinstance(indexBlock, bool), 'Invalid index block flag %s' % indexBlock
        assert isinstance(indexPrepare, bool), 'Invalid index prepare flag %s' % indexPrepare
        
        assert isinstance(indexAttributesCapture, dict), 'Invalid index attributes capture %s' % indexAttributesCapture
        
        indexAdjust, indexBlock = self._adjust, indexBlock and not self._adjust
        indexPrepare = indexBlock and indexPrepare
        self._adjust = False

        if indexAdjust: self._at(JSON_BLOCK_JOIN)
        
        if not self._first:
            if self._block or indexBlock: ablock = self._start(JSON_BLOCK_ADJUST)
            self._out.write(',')
            if self._block or indexBlock:
                self._end(ablock)
                self._block = indexBlock
        else: self._block = indexBlock
        
        if indexBlock: iblock = self._start(NAME_BLOCK, name)
        if self._stack and self._stack[0][0]:
            if indexPrepare:
                pprepare = self._start(JSON_PREPARE_PROPERTY)
                nprepare = self._start(JSON_PREPARE_NAME, offset=1)  # offset +1 for the comma
            self._out.write('"%s"' % name)
            if indexPrepare: self._end(nprepare, offset= -1)  # offset -1 for the comma
            self._out.write(':')
            if indexPrepare: self._end(pprepare)
        else:
            if indexPrepare: self._at(JSON_PREPARE_NAME_FIXED, name)
            if indexAdjust: self._at(JSON_ADJUST_PROPERTY)
        self._out.write('{')
        if indexAdjust: self._at(JSON_ADJUST_ATTRIBUTES)
        
        self._first = True
        
        if attributes:
            if indexPrepare: iprepare = self._start(JSON_PREPARE_ATTRIBUTES)
            for nameAttr, valueAttr in attributes.items():
                assert isinstance(nameAttr, str), 'Invalid attribute name %s' % nameAttr
                assert isinstance(valueAttr, str), 'Invalid attribute value %s' % valueAttr

                if self._first: self._first = False
                else: self._out.write(',')
                self._out.write('"%s"' % nameAttr)
                self._out.write(':')
                if nameAttr in indexAttributesCapture:
                    iattr = self._start(indexAttributesCapture[nameAttr], offset=1)  # offset +1 for the comma
                    self._out.write(encode_basestring(valueAttr))
                    self._end(iattr, offset= -1)  # offset -1 for the comma
                else: self._out.write(encode_basestring(valueAttr))
            if indexPrepare: self._end(iprepare)
        
        if not isObject:
            if not self._first: self._out.write(',')
            if indexAdjust: iadjust = self._start(JSON_ADJUST_NAME, offset=1)  # offset +1 for the comma
            self._out.write('"%s"' % name)
            if indexAdjust: self._end(iadjust, offset= -1)  # offset -1 for the comma
            self._out.write(':[')
            self._first = True
        
        self._stack.appendleft((isObject, iblock if indexBlock else None))
    
    # ----------------------------------------------------------------
    
    def _at(self, marker, value=None, offset=0):
        '''
        Creates an index that starts and ends at the current offset.
        '''
        self._indexes.append(Index(marker, self._outb.tell() + offset, value))
        
    def _start(self, marker, value=None, offset=0):
        '''
        Starts and index at the current offset.
        '''
        index = Index(marker, self._outb.tell() + offset, value)
        self._indexes.append(index)
        return index
        
    def _end(self, index, offset=0):
        '''
        Ends the ongoing index at the current offset.
        '''
        assert isinstance(index, Index), 'Invalid index %s' % index
        index.end = self._outb.tell() + offset
