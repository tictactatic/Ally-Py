'''
Created on Aug 3, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the JSON encoder processor handler.
'''

from .base import RenderBaseHandler
from ally.container.ioc import injected
from ally.core.spec.transform.render import IRender
from ally.support.util_io import IOutputStream
from codecs import getwriter
from collections import deque
from json.encoder import encode_basestring

# --------------------------------------------------------------------

@injected
class RenderJSONHandler(RenderBaseHandler):
    '''
    Provides the JSON encoding.
    @see: RenderBaseHandler
    '''

    encodingError = 'backslashreplace'
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

        return RenderJSON(getwriter(charSet)(output, self.encodingError))

# --------------------------------------------------------------------

class RenderJSON(IRender):
    '''
    Renderer for JSON.
    '''
    __slots__ = ('out', 'isObject', 'isFirst')

    def __init__(self, out):
        '''
        Construct the text object renderer.
        
        @param out: file writer
            The writer to place the JSON.
        '''
        assert out, 'Invalid JSON output stream %s' % out

        self.out = out
        self.isObject = deque()
        self.isFirst = True

    def property(self, name, value):
        '''
        @see: IRender.property
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(value, (str, list, dict)), 'Invalid value %s' % value
        assert self.isObject and self.isObject[0], 'No object for property'

        if self.isFirst: self.isFirst = False
        else: self.out.write(',')
        self.out.write(encode_basestring(name))
        self.out.write(':')
        if isinstance(value, list): value = '[%s]' % ','.join(encode_basestring(item) for item in value)
        elif isinstance(value, dict):
            value = ','.join('%s:%s' % (encode_basestring(key), encode_basestring(item)) for key, item in value.items())
            value = '{%s}' % value
        else:
            value = encode_basestring(value)
        self.out.write(value)

    def beginObject(self, name, attributes=None):
        '''
        @see: IRender.beginObject
        '''
        self.openObject(name, attributes)
        self.isObject.appendleft(True)
        
        return self

    def beginCollection(self, name, attributes=None):
        '''
        @see: IRender.beginCollection
        '''
        assert isinstance(name, str), 'Invalid name %s' % name

        self.openObject(name, attributes)
        if not self.isFirst: self.out.write(',')
        self.out.write(encode_basestring(name))
        self.out.write(':[')
        self.isFirst = True
        self.isObject.appendleft(False)
        
        return self

    def end(self):
        '''
        @see: IRender.collectionEnd
        '''
        assert self.isObject, 'No collection to end'
        if self.isObject.popleft(): self.out.write('}')
        else: self.out.write(']}')
        
    # ----------------------------------------------------------------

    def openObject(self, name, attributes=None):
        '''
        Used to open a JSON object.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert attributes is None or isinstance(attributes, dict), 'Invalid attributes %s' % attributes
        out = self.out

        if not self.isFirst: out.write(',')

        if self.isObject and self.isObject[0]:
            out.write(encode_basestring(name))
            out.write(':')

        out.write('{')
        self.isFirst = True
        if attributes:
            for attrName, attrValue in attributes.items():
                assert isinstance(attrName, str), 'Invalid attribute name %s' % attrName
                assert isinstance(attrValue, str), 'Invalid attribute value %s' % attrValue

                if self.isFirst: self.isFirst = False
                else: out.write(',')
                out.write(encode_basestring(attrName))
                out.write(':')
                out.write(encode_basestring(attrValue))
