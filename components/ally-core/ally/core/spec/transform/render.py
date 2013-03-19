'''
Created on Jun 27, 2012

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides transforming object to rendered content. 
'''

from collections import deque
import abc

# --------------------------------------------------------------------

class IRender(metaclass=abc.ABCMeta):
    '''
    The specification for the renderer of encoded objects.
    '''
    __slots__ = ()

    @abc.abstractclassmethod
    def property(self, name, value):
        '''
        Called to signal that a property value has to be rendered.

        @param name: string
            The property name.
        @param value: string|tuple(string)|list[string]|dictionary{string: string}
            The value.
        '''

    @abc.abstractclassmethod
    def beginObject(self, name, attributes=None):
        '''
        Called to signal that an object has to be rendered.
        
        @param name: string
            The object name.
        @param attributes: dictionary{string, string}|None
            The attributes for the value.
        @return: self
            The same render instance for chaining purposes.
        '''

    @abc.abstractclassmethod
    def beginCollection(self, name, attributes=None):
        '''
        Called to signal that a collection of objects has to be rendered.
        
        @param name: string
            The collection name.
        @param attributes: dictionary{string, string}|None
            The attributes for the collection.
        @return: self
            The same render instance for chaining purposes.
        '''

    @abc.abstractclassmethod
    def end(self):
        '''
        Called to signal that the current block has ended the rendering.
        '''

class Value:
    '''
    Container for the text value.
    '''
    __slots__ = ('name', 'value')

    def __init__(self, name, value):
        '''
        Construct the text value.
        
        @param name: string
            The name for the value.
        @param value: string
            The value.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(value, str), 'Invalid value %s' % value

        self.name = name
        self.value = value

class Object:
    '''
    Container for a text object.
    '''
    __slots__ = ('name', 'properties', 'attributes')

    def __init__(self, name, *properties, attributes=None):
        '''
        Construct the text object.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert attributes is None or isinstance(attributes, dict), 'Invalid attributes %s' % attributes

        self.name = name
        self.properties = properties
        self.attributes = attributes

class List:
    '''
    Container for a text collection.
    '''
    __slots__ = ('name', 'items', 'attributes')

    def __init__(self, name, *items, attributes=None):
        '''
        Construct the text list.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert attributes is None or isinstance(attributes, dict), 'Invalid attributes %s' % attributes

        self.name = name
        self.items = items
        self.attributes = attributes

# --------------------------------------------------------------------

class RenderToObject(IRender):
    '''
    A @see: IRender implementation that captures the data into a text object.
    '''
    __slots__ = ('obj', 'stack')

    def __init__(self):
        '''
        Construct the render.
        '''
        self.stack = deque()
        self.obj = None

    def property(self, name, value):
        '''
        @see: IRender.property
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(value, (str, list, dict)), 'Invalid value %s' % value
        if __debug__:
            if isinstance(value, list):
                for item in value: assert isinstance(item, str), 'Invalid list item %s' % item
            elif isinstance(value, dict):
                for key, item in value.items():
                    assert isinstance(key, str), 'Invalid dictionary key %s' % key
                    assert isinstance(item, str), 'Invalid dictionary value %s' % item
        assert self.stack, 'No object available on stack'
        
        obj = self.stack[0]
        assert isinstance(obj, dict), 'No object to set the property on'
        obj[name] = value

    def beginObject(self, name, attributes=None):
        '''
        @see: IRender.beginObject
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert attributes is None or isinstance(attributes, dict), 'Invalid attributes %s' % attributes

        value = {}
        if attributes:
            for attrName, attrValue in attributes.items():
                assert isinstance(attrName, str), 'Invalid attribute name %s' % attrName
                assert isinstance(attrValue, str), 'Invalid attribute value %s' % attrValue
            value.update(attributes)
            
        if self.stack:
            obj = self.stack[0]
            if isinstance(obj, dict): obj[name] = value
            else: obj.append(value)
        else: self.obj = value
        self.stack.appendleft(value)
        
        return self

    def collectionStart(self, name, attributes=None):
        '''
        @see: IRender.collectionStart
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert attributes is None or isinstance(attributes, dict), 'Invalid attributes %s' % attributes

        valueObj = {}
        if attributes:
            for attrName, attrValue in attributes.items():
                assert isinstance(attrName, str), 'Invalid attribute name %s' % attrName
                assert isinstance(attrValue, str), 'Invalid attribute value %s' % attrValue
            valueObj.update(attributes)

        value = valueObj[name] = []
        if self.stack:
            obj = self.stack[0]
            assert isinstance(obj, dict), 'Not an object to set the collection on'
            obj[name] = valueObj
        else: self.obj = valueObj
        self.stack.appendleft(value)
        
        return self

    def end(self):
        '''
        @see: IRender.end
        '''
        assert self.stack, 'No object available on stack to end'

        self.stack.popleft()

# --------------------------------------------------------------------

def renderObject(txt, render):
    '''
    Renders the text object on to the provided renderer.
    
    @param txt: Value, Object, List
        The text object to render.
    @param renderer: IRender
        The renderer to render to.
    '''
    assert isinstance(render, IRender), 'Invalid render %s' % render

    if isinstance(txt, Value):
        assert isinstance(txt, Value)

        render.property(txt.name, txt.value)

    elif isinstance(txt, Object):
        assert isinstance(txt, Object)

        render.beginObject(txt.name, txt.attributes)
        for prop in txt.properties: renderObject(prop, render)
        render.end()

    elif isinstance(txt, List):
        assert isinstance(txt, List)

        render.beginCollection(txt.name, txt.attributes)
        for item in txt.items: renderObject(item, render)
        render.end()

    else: raise ValueError('Invalid text object %s' % txt)
