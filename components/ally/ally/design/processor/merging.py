'''
Created on Feb 12, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the merging support functions.
'''

from .context import Object
from .spec import IAttribute, ContextMetaClass, AttrError, IProcessor
from collections import Iterable

# --------------------------------------------------------------------

TRACK_ATTRIBUTES = False
# Flag indicating that the attribute merging and solving should be tracked for debuging purposes.

class AttributeTracker(IAttribute):
    '''
    Proxy implementation for an attribute that provides processing tracking.
    '''
    __slots__ = ('wrapped', 'mergedBy', 'solvedBy')
    
    def __init__(self, wrapped):
        '''
        Construct the tracking attribute for the wrapped attribute.
        
        @param wrapped: IAttribute
            The attribute to wrap.
        '''
        assert isinstance(wrapped, IAttribute), 'Invalid wrapped attribute %s' % wrapped
        self.wrapped = wrapped
        self.mergedBy = []
        self.solvedBy = []
        
    def merge(self, other, isFirst=True):
        '''
        @see: IAttribute.merge
        '''
        try: 
            if isinstance(other, AttributeTracker):
                assert isinstance(other, AttributeTracker)
                attribute = AttributeTracker(self.wrapped.merge(other.wrapped, isFirst))
                attribute.mergedBy.extend(other.mergedBy)
                attribute.solvedBy.extend(other.solvedBy)
            else:
                attribute = AttributeTracker(self.wrapped.merge(other, isFirst))
                
        except AttrError:
            raise AttrError('Error in merging %s\n\nwith %s' % (self, other))
        
        for processor in self.mergedBy: attribute.addMerged(processor)
        for processor in self.solvedBy: attribute.addSolved(processor)
        return attribute
    
    def solve(self, other):
        '''
        @see: IAttribute.solve
        '''
        if isinstance(other, AttributeTracker):
            assert isinstance(other, AttributeTracker)
            attribute = AttributeTracker(self.wrapped.solve(other.wrapped))
            attribute.mergedBy.extend(other.mergedBy)
            attribute.solvedBy.extend(other.solvedBy)
        else:
            attribute = AttributeTracker(self.wrapped.solve(other))
            
        for processor in self.mergedBy: attribute.addMerged(processor)
        for processor in self.solvedBy: attribute.addSolved(processor)
        return attribute
    
    def isForObject(self):
        '''
        @see: IAttribute.isForObject
        '''
        return self.wrapped.isForObject()
    
    def place(self, clazz, name, asDefinition):
        '''
        @see: IAttribute.place
        '''
        raise AttrError('Cannot place the tracked attribute')
        
    def isAvailable(self, clazz, name):
        '''
        @see: IAttribute.isAvailable
        '''
        return self.wrapped.isAvailable(clazz, name)
        
    def isValid(self, value):
        '''
        @see: IAttribute.isValid
        '''
        return self.wrapped.isValid(value)
    
    def isUsed(self):
        '''
        @see: IAttribute.isUsed
        '''
        return self.wrapped.isUsed()

    # ----------------------------------------------------------------
    
    def addMerged(self, processor):
        '''
        Adds a new processor to the processed by list.
        
        @param processor: object
            The processor to add.
        @return: self
            The same instance for chaining purposes.
        '''
        if processor:
            assert isinstance(processor, IProcessor), 'Invalid processor %s' % processor
            if not processor in self.mergedBy: self.mergedBy.append(processor)
        return self
    
    def addSolved(self, processor):
        '''
        Adds a new processor to the processed by list.
        
        @param processor: object
            The processor to add.
        @return: self
            The same instance for chaining purposes.
        '''
        if processor:
            assert isinstance(processor, IProcessor), 'Invalid processor %s' % processor
            if not processor in self.solvedBy: self.solvedBy.append(processor)
        return self

    def __str__(self):
        st = []
        if self.mergedBy:
            st.append('merged by %s' % '\n'.join((str(proc) for proc in self.mergedBy)))
        else: st.append('never merged')
        if self.solvedBy:
            st.append('solved by %s' % '\n'.join((str(proc) for proc in self.solvedBy)))
        else: st.append('never solved')
                    
        return '%s%s' % (str(self.wrapped), '\n\n'.join(st))

# --------------------------------------------------------------------

def iterateAttributes(contexts):
    '''
    Iterate the attributes of the provided contexts.
    
    @param contexts: dictionary{string, ContextMetaClass)
        The contexts to have the attributes iterated.
    @param processor: object|None
        The processor that makes the processing, this is for tracking usage in debug mode.
    @return: Iterable(tuple(string, string), IAttribute)
        The attributes iterator.
    '''
    assert isinstance(contexts, dict), 'Invalid contexts %s' % contexts

    for nameContext, context in contexts.items():
        assert isinstance(nameContext, str), 'Invalid context name %s' % nameContext
        assert isinstance(context, ContextMetaClass), 'Invalid context class %s' % context

        for nameAttribute, attribute in context.__attributes__.items():
            assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
            if TRACK_ATTRIBUTES: attribute = AttributeTracker(attribute)
            yield (nameContext, nameAttribute), attribute

# --------------------------------------------------------------------

def mergeAttributes(main, other, processor=None):
    '''
    Merges into the provided attributes the other attributes.
    
    @param main: dictionary{tuple(string, string), IAttribute}
        The main attributes to merge to.
    @param other: Iterable(tuple(string, string), IAttribute)
        The iterable yielding attributes like structure. This attributes will be merged into the main attributes.
    @param processor: object|None
        The processor that makes the processing, this is for tracking usage in debug mode.
    @return: dictionary{tuple(string, string), IAttribute}
        Provides the main dictionary.
    '''
    assert isinstance(main, dict), 'Invalid main attributes %s' % main
    if isinstance(other, dict): other = other.items()
    assert isinstance(other, Iterable), 'Invalid other attributes %s' % other

    for key, attribute in other:
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        assert isinstance(key, tuple), 'Invalid key %s' % key

        attr = main.get(key)
        if attr is None: main[key] = attribute
        else:
            assert isinstance(attr, IAttribute), 'Invalid attribute %s' % attr 
            main[key] = attr.merge(attribute)
            if TRACK_ATTRIBUTES and isinstance(main[key], AttributeTracker): main[key].addMerged(processor)
            
    return main

def solveAttributes(main, other, processor=None):
    '''
    Solves into the provided attributes the other attributes.
    
    @param main: dictionary{tuple(string, string), IAttribute}
        The main attributes to solve to.
    @param other: Iterable(tuple(string, string), IAttribute)
        The iterable yielding attributes like structure. This attributes will be merged into the main attributes.
    @param processor: object|None
        The processor that makes the processing, this is for tracking usage in debug mode.
    @return: dictionary{tuple(string, string), IAttribute}
        Provides the main dictionary.
    '''
    assert isinstance(main, dict), 'Invalid main attributes %s' % main
    if isinstance(other, dict): other = other.items()
    assert isinstance(other, Iterable), 'Invalid other attributes %s' % other

    for key, attribute in other:
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        assert isinstance(key, tuple), 'Invalid key %s' % key
        
        attr = main.get(key)
        if attr is None: main[key] = attribute
        else:
            main[key] = attribute.solve(attr)
            if TRACK_ATTRIBUTES and isinstance(main[key], AttributeTracker): main[key].addSolved(processor)
    return main

# --------------------------------------------------------------------

def extract(attributes, contextName):
    '''
    Extracts the attributes for the provided context name.
    
    @param attributes: Iterable(tuple(string, string), IAttribute)
        The iterable yielding attributes like structure. From this attributes will be extracted the attributes for
        the provided context name.
    @param contextName: string
        The context name to extract for.
    @return: Iterable(tuple(string, string), IAttribute)
        The extracted attributes.
    '''
    if isinstance(attributes, dict): attributes = attributes.items()
    assert isinstance(attributes, Iterable), 'Invalid attributes %s' % attributes
    assert isinstance(contextName, str), 'Invalid context name %s' % contextName
    
    for key, attribute in attributes:
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        nameContext, _nameAttribute = key
        if nameContext == contextName: yield key, attribute

def validateForObject(attributes):
    '''
    Validates the attribute in order to be used for an Object context.
    
    @param attributes: Iterable(tuple(string, string), IAttribute)
        The iterable yielding attributes like structure. This attributes will be checked for the Object contexts.
    '''
    if isinstance(attributes, dict): attributes = attributes.items()
    assert isinstance(attributes, Iterable), 'Invalid attributes %s' % attributes
    for _key, attribute in attributes:
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        if not attribute.isForObject(): raise AttrError('Unsolved %s' % attribute)

def createObject(attributes):
    '''
    Creates Object context classes based on the provided main attributes.
    
    @param attributes: Iterable(tuple(string, string), IAttribute)
        The iterable yielding attributes like structure. This attributes will be used for creating the Object contexts.
    @return: dictionary{string, ContextMetaClass}
        The dictionary containing the created Object class indexed by context name.
    '''
    if isinstance(attributes, dict): attributes = attributes.items()
    assert isinstance(attributes, Iterable), 'Invalid attributes %s' % attributes
    
    namespaces = {}
    for key, attribute in attributes:
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        if TRACK_ATTRIBUTES and isinstance(attribute, AttributeTracker): attribute = attribute.wrapped
        if not attribute.isForObject(): raise AttrError('Unsolved %s' % attribute)
        nameContext, nameAttribute = key

        namespace = namespaces.get(nameContext)
        if namespace is None: namespace = namespaces[nameContext] = dict(__module__=__name__)
        namespace[nameAttribute] = attribute

    return {name: type('Object$%s%s' % (name[0].upper(), name[1:]), (Object,), namespace)
            for name, namespace in namespaces.items()}
