'''
Created on Feb 11, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the processor specifications.
'''

from ally.support.util import immut, firstOf
from collections import Iterable
import abc

# --------------------------------------------------------------------

class AttrError(Exception):
    '''
    Raised when there is an attribute problem.
    '''

class ProcessorError(Exception):
    '''
    Raised when there is a processor problem.
    '''
    
class AssemblyError(Exception):
    '''
    Raised when there is an assembly problem.
    '''
    
# --------------------------------------------------------------------

class IAttribute(metaclass=abc.ABCMeta):
    '''
    The attribute specification.
    '''
    
    @abc.abstractmethod
    def merge(self, other, isFirst=True):
        '''
        Merges this attribute with the other attribute.
        
        @param other: IAttribute
            The attribute to merge with.
        @param isFirst: boolean
            Flag indicating that if this attribute is the first one in the merging process, in many cases is very important
            who gets merged with whom.
        @return: IAttribute
            The attribute obtained by combining this attribute and the other attribute.
        '''
        
    @abc.abstractmethod
    def solve(self, other):
        '''
        Solve this attribute with the other attribute. The solving it differs from merging because the attributes need to
        complete each other.
        
        @param other: IAttribute
            The attribute to solve with.
        @return: IAttribute
            The attribute obtained by solving this attribute with the other attribute.
        '''
    
    @abc.abstractmethod
    def place(self, clazz, name, asDefinition):
        '''
        Places the appropriate descriptor on the provided class based on this attribute. Attention the placed descriptors
        are required to contain a '__name__' and '__objclass__' attributes in order to be usable in the '__contains__'
        context method. When placing for an Object context then a check for an already existing descriptor must be done
        since usually '__slots__' is used for Object contexts.
        
        @param clazz: class
            The class to place the descriptor on.
        @param name: string
            The name of the descriptor to place.
        @param asDefinition: boolean
            Flag indicating that the attribute is as definition only and no instances for the provided class will be created.
        '''
    
    @abc.abstractmethod
    def isCreatable(self):
        '''
        Checks if this attribute can be used for contexts that can have object created.
        
        @return: boolean
            True if it can be added on context with objects, False otherwise.
        '''
    
    @abc.abstractmethod
    def isAvailable(self, clazz, name):
        '''
        Checks if this attribute is in for the provided class as the attribute name.
        
        @param clazz: class
            The class to check.
        @param name: string
            The name of the attribute.
        @return: boolean
            True if the attribute is valid, False if the attribute is not known for the provided class.
        '''
        
    @abc.abstractmethod
    def isValid(self, value):
        '''
        Checks if this value is valid for this attribute.
        
        @param value: object
            The value to check.
        @return: boolean
            True if the value is valid, False otherwise.
        '''
        
    @abc.abstractmethod
    def isUsed(self):
        '''
        Checks if the attribute is not used.
        
        @return: boolean
            True if the attribute is used, False otherwise.
        '''
    
class IDefiner(metaclass=abc.ABCMeta):
    '''
    The context definer specification, the implementations for this specification will be used in constructing the context
    classes.
    '''
    
    @abc.abstractmethod
    def process(self, name, bases, namespace):
        '''
        Process the provided context definition parameters.
        
        @param name: string
            The class name.
        @param bases: tuple(class)
            The inherited classes.
        @param namespace: dictionary{string, object}
            The context name space definition.
        @return: tuple(string, tuple(classes), dictionary{string, object})
            The name, basses and namespace to use in construccting the context class.
        '''
    
    @abc.abstractmethod
    def finalize(self, clazz):
        '''
        Finalizes the context class definition.
        
        @param clazz: ContextMetaClass
            The context meta class to finalize the definition for.
        '''

class ContextMetaClass(abc.ABCMeta):
    '''
    Used for the context objects to behave like a data container only.
    The context can be checked against any object that has the specified attributes with values of the specified 
    classes instance.
    '''

    def __new__(cls, name, bases, namespace):
        if not bases:
            definer = namespace.pop('__definer__', None)
            if not definer: raise TypeError('Invalid context definition, has no __definer__')
            self = super().__new__(cls, name, bases, namespace)
            self.__definer__ = definer
            self.__attributes__ = immut()
            return self

        definer = namespace.get('__definer__')
        if not definer:
            first = bases[0]
            if not isinstance(first, ContextMetaClass):
                raise TypeError('The first inherited class need to be a context class, invalid class %s' % first)
            assert isinstance(first, ContextMetaClass)
            definer = first.__definer__
        
        assert isinstance(definer, IDefiner), 'Invalid definer %s' % definer
        
        self = super().__new__(cls, *definer.process(name, bases, namespace))
        definer.finalize(self)
        
        return self
    
    def __str__(self):
        return '<context \'%s.%s(%s)\'>' % (self.__module__, self.__name__, ', '.join(self.__attributes__))

# --------------------------------------------------------------------

class Attributes:
    '''
    Contextual attributes repository.
    '''
    __slots__ = ('_attributes', '_locked')
    
    def __init__(self, locked=False, contexts=None):
        '''
        Construct the attributes repository.

        @param locked: boolean
            If True then the attributes cannot be modified.
        @param contexts: dictionary{string, ContextMetaClass)|None
            The contexts to have the attributes created based on.
        '''
        assert isinstance(locked, bool), 'Invalid locked flag %s' % locked
        self._attributes = {}
        self._locked = locked
        
        if contexts is not None:
            assert isinstance(contexts, dict), 'Invalid contexts %s' % contexts
            for nameContext, context in contexts.items():
                assert isinstance(nameContext, str), 'Invalid context name %s' % nameContext
                assert isinstance(context, ContextMetaClass), 'Invalid context class %s' % context
        
                for nameAttribute, attribute in context.__attributes__.items():
                    assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
                    self._attributes[(nameContext, nameAttribute)] = attribute
                    
    def lock(self):
        '''
        Locks this attributes repository.
        '''
        self._locked = True
                    
    def merge(self, other, joined=True):
        '''
        Merges into this attributes the provided attributes.
        
        @param other: Attributes|dictionary{string, ContextMetaClass)
            The attributes or dictionary of context to merge with.
        @param joined: boolean
            If True then the other attributes that are not found in this attributes repository will be added, if False
            the merging is done only on existing attributes in this repository.
        '''
        if self._locked: raise AttrError('Attributes locked')
        if not isinstance(other, Attributes): other = Attributes(True, other)
        assert isinstance(other, Attributes), 'Invalid other attributes %s' % other
        assert isinstance(joined, bool), 'Invalid joined flag %s' % joined
    
        for key, attribute in other._attributes.items():
            assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
            assert isinstance(key, tuple), 'Invalid key %s' % key
    
            attr = self._attributes.get(key)
            if attr is None:
                if joined: self._attributes[key] = attribute
            else:
                assert isinstance(attr, IAttribute), 'Invalid attribute %s' % attr 
                self._attributes[key] = attr.merge(attribute)
                
    def solve(self, other, joined=True):
        '''
        Solves into this attributes the provided attributes.
        
        @param other: Attributes|dictionary{string, ContextMetaClass)
            The attributes or dictionary of context to solve with.
        @param joined: boolean
            If True then the other attributes that are not found in this attributes repository will be added, if False
            the solving is done only on existing attributes in this repository.
        '''
        if self._locked: raise AttrError('Attributes locked')
        if not isinstance(other, Attributes): other = Attributes(True, other)
        assert isinstance(other, Attributes), 'Invalid other attributes %s' % other
        assert isinstance(joined, bool), 'Invalid joined flag %s' % joined
    
        for key, attribute in other._attributes.items():
            assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
            assert isinstance(key, tuple), 'Invalid key %s' % key
            
            attr = self._attributes.get(key)
            if attr is None:
                if joined: self._attributes[key] = attribute
            else: self._attributes[key] = attribute.solve(attr)
    
    # ----------------------------------------------------------------
    
    def copy(self, names=None):
        '''
        Creates a copy for this attributes repository, if this repository has the locked flag it will no be passed on to the copy.
        
        @param names: Iterable(string|tuple(string, string))|None
            The context or attribute names to copy the attributes for, if None then all attributes are copied.
        @return: Attributes
            The cloned attributes repository.
        '''
        copy = Attributes()
        if names:
            assert isinstance(names, Iterable), 'Invalid names %s' % names
            for name in names:
                if isinstance(name, tuple):
                    attr = self._attributes.get(name)
                    if attr: copy._attributes[name] = attr
                else:
                    assert isinstance(name, str), 'Invalid context or attribute name %s' % name
                    for key, attr in self._attributes.items():
                        if key[0] == name: copy._attributes[key] = attr
        else:
            copy._attributes.update(self._attributes)
            
        return copy
    
    def extract(self, names):
        '''
        Extracts from this attributes repository all the attributes for the provided context or attribute names.
        
        @param names: Iterable(string|tuple(string, string))
            The context or attribute names to extract the attributes for.
        @return: Attributes
            The extracted attributes repository.
        '''
        if self._locked: raise AttrError('Attributes locked')
        assert isinstance(names, Iterable), 'Invalid names %s' % names
        
        toExtract = []
        for name in names:
            if isinstance(name, tuple):
                if name in self._attributes: toExtract.append(name)
            else:
                assert isinstance(name, str), 'Invalid context or attribute name %s' % name
                for key in self._attributes:
                    if key[0] == name: toExtract.append(key)
                
        extracted = Attributes()
        for key in toExtract: extracted._attributes[key] = self._attributes.pop(key)
        
        return extracted
    
    # ----------------------------------------------------------------
    
    def validate(self):
        '''
        Validates the attributes in this repository.
        '''
        for key, attribute in self._attributes.items():
            assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
            if not attribute.isCreatable(): raise AttrError('The \'%s.%s\' unsolved for %s' % (key + (attribute,)))
    
    def iterateNames(self):
        '''
        Iterates the attributes names for this attributes repository.
        
        @return: Iterable(tuple(string, string))
            The attributes names iterator.
        '''
        return self._attributes.keys()
    
    def iterate(self):
        '''
        Iterates the attributes for this attributes repository.
        
        @return: Iterable(tuple(string, string), IAttribute)
            The attributes iterator.
        '''
        return self._attributes.items()
    
    # ----------------------------------------------------------------
    
    def __str__(self):
        return '%s:\n%s' % (self.__class__.__name__,
                    ''.join('%s.%s with %s' % (key + (attr,)) for key, attr in sorted(self._attributes.items(), key=firstOf)))
            
class IReport(metaclass=abc.ABCMeta):
    '''
    Provides the reporting support.
    '''
    
    def open(self, name):
        '''
        Open a new report for the provided name.
        
        @param name: string
            The name for the created report.
        @return: IReport
            The report for name.
        '''
        
    def add(self, attributes):
        '''
        Adds the provided attributes to be reported on.
        
        @param attributes: Attributes
            The attributes to be reported.
        '''

class IProcessor(metaclass=abc.ABCMeta):
    '''
    The processor specification.
    '''
    
    @abc.abstractmethod
    def register(self, sources, attributes, extensions, calls, report):
        '''
        Register the processor call. The processor needs to alter the attributes and extensions dictionaries based on the
        processor.
        
        @param sources: Attributes
            The sources attributes that need to be solved by processors.
        @param attributes: Attributes
            The attributes solved so far by processors.
        @param extensions: Attributes
            The attributes that are not part of the main stream attributes but they are rather extension for the created
            contexts.
        @param report: IReport
            The report to be used in the registration process.
        @param calls: list[callable]
            The list of callable objects to register the processor call into.
        '''
