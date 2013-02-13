'''
Created on Feb 11, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the processor specifications.
'''

from ally.support.util import immut
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
    def isForObject(self):
        '''
        Checks if this attribute can be used for contexts that can have object created.
        
        @return: boolean
            True if it can be added on context with objects, False otherwise.
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

class IProcessor(metaclass=abc.ABCMeta):
    '''
    The processor specification.
    '''
    
    @abc.abstractmethod
    def register(self, contexts, attributes, calls):
        '''
        Register the processor call. The processor also needs to register the contexts that are used by the call into the
        provided attributes.
        
        @param contexts: dictionary{string, ContextMetaClass}
            The contexts that need to be solved by processors.
        @param attributes: dictionary{tuple(string, string), IAttribute}
            The attributes that are so far generated by processors, whenever registration is made this dictionary needs
            to be merged with the processor contexts attributes. The key is formed as a tuple having on the first position
            the context name and in the second position the attribute name.
        @param calls: list[callable]
            The list of callable objects to register the processor call into.
        ''' 
