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
# Standard flags

LIST_UNAVAILABLE = 'List unavailable attributes'
# Flag indicating that the unavailable attributes names should be iterated.
LIST_UNUSED = 'List unused attributes'
# Flag indicating that the unused attributes names should be iterated.
LIST_CLASSES = 'List used in classes for attributes'
# Flag indicating that the classes where an attribute is used should be provided as a value.

CREATE_DEFINITION = 'Create definition attributes'
# Flag indicating that definition attributes need to be created.

# --------------------------------------------------------------------

class AttrError(Exception):
    '''
    Raised when there is an attribute problem.
    '''
    
class ResolverError(Exception):
    '''
    Raised when there is an resolver problem.
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

class IResolver(metaclass=abc.ABCMeta):
    '''
    The context resolver specification. The resolvers implementations need to be of a immutable nature.
    '''
    __slots__ = ()
        
    @abc.abstractmethod
    def copy(self, names=None):
        '''
        Create a copy of this context resolver.
        
        @param names: Iterable(string)|None
            The attribute names to copy for, if a name is not known then is ignored, if None then all attributes are copied.
        @return: IResolver
            The copy (with the provided names) of the context resolver.
        '''

    @abc.abstractmethod
    def merge(self, other, isFirst=True):
        '''
        Merges this context resolver with the other context resolver.
        
        @param other: IResolver
            The context resolver to merge with.
        @param isFirst: boolean
            Flag indicating that if this context resolver is the first one in the merging process, in many cases is very 
            important who gets merged with whom.
        @return: IResolver
            The context resolver obtained by merging this context resolver and the other context resolver.
        '''
        
    @abc.abstractmethod
    def solve(self, other):
        '''
        Solve this context resolver with the other context resolver. The solving it differs from merging because the 
        resolvers need to complete each other.
        
        @param other: IResolver
            The context resolver to solve with.
        @return: IResolver
            The context resolver obtained by solving this context resolver with the other context resolver.
        '''
        
    @abc.abstractmethod
    def list(self, *flags):
        '''
        Lists the attributes names for this context resolver.
        
        @param flags: arguments[object]
            Flags indicating specific attributes to be listed, if no specific flag is provided then all attributes are listed.
        @return: dictionary{string: object}
            The attribute names of this context resolver in respect with the provided flag, also provides other information
            depending on the provided flag.
        '''
    
    @abc.abstractmethod
    def create(self, *flags):
        '''
        Create the attributes to be used on a new context.
        
        @param flags: arguments[object]
            Flags to be used for creating the attributes.
        @return: dictionary{string: IAttribute}
            The attributes dictionary specific for this context resolver.
        '''

# --------------------------------------------------------------------
        
class IAttribute(metaclass=abc.ABCMeta):
    '''
    The attribute specification, all valid attributes located in a class need to define the: '__name__', '__objclass__'.
    '''
    __slots__ = ('__name__', '__objclass__')
    
    @abc.abstractmethod
    def resolver(self):
        '''
        Provides the resolver class specific for this attribute.
        
        @return: sub class of IResolver
            The resolver class of this attribute, this class has to have receive in the constructor the context class that has
            to resolve.
        '''
    
    @abc.abstractmethod
    def place(self, clazz, name):
        '''
        Places the appropriate descriptor on the provided class based on this attribute. Attention the placed definition 
        descriptors are required to contain a '__name__' and '__objclass__' attributes in order to be usable in the '__contains__'
        context method.
        
        @param clazz: class
            The class to place the descriptor on.
        @param name: string
            The name of the descriptor to place.
        '''
    
    @abc.abstractmethod
    def isValid(self, clazz):
        '''
        Checks if the provided class is valid for this attribute.
        
        @param clazz: class
            The class to check.
        @return: boolean
            True if the attribute is valid, False if the attribute is not known for the provided class.
        '''
        
    @abc.abstractmethod
    def isIn(self, clazz):
        '''
        Checks if the provided class contains this attribute.
        
        @param clazz: class
            The class to check.
        @return: boolean
            True if the attribute is contained, False if the attribute is not known for the provided class.
        '''

class IReport(metaclass=abc.ABCMeta):
    '''
    Provides the reporting support.
    '''
    __slots__ = ()
    
    def open(self, name):
        '''
        Open a new report for the provided name.
        
        @param name: string
            The name for the created report.
        @return: IReport
            The report for name.
        '''
        
    def add(self, resolvers):
        '''
        Adds the provided resolvers to be reported on.
        
        @param resolvers: dictionary{string: IResolver}
            The resolvers to be reported.
        '''

class IProcessor(metaclass=abc.ABCMeta):
    '''
    The processor specification.
    '''
    
    @abc.abstractmethod
    def register(self, sources, resolvers, extensions, calls, report):
        '''
        Register the processor call. The processor needs to alter the attributes and extensions dictionaries based on the
        processor.
        
        @param sources: dictionary{string: IResolver}
            The sources resolvers that need to be solved by processors.
        @param resolvers: dictionary{string: IResolver}
            The resolvers used in creating the final contexts.
        @param extensions: dictionary{string: IResolver}
            The resolvers that are not part of the current resolvers but they are rather extension for the final contexts.
        @param calls: list[callable]
            The list of callable objects to register the processor call into.
        @param report: IReport
            The report to be used in the registration process.
        '''

class IFinalizer(metaclass=abc.ABCMeta):
    '''
    The processor finalizer specification.
    '''
    
    @abc.abstractmethod
    def finalized(self, sources, resolvers, extensions, report):
        '''
        The processor finalized action on the resolvers.
        
        @param sources: dictionary{string: IResolver}
            The sources resolvers that have been solved by processors.
        @param resolvers: dictionary{string: IResolver}
            The resolvers used in creating the final contexts.
        @param extensions: dictionary{string: IResolver}
            The resolvers that are not part of the current resolvers but they are rather extension for the final contexts.
        @param report: IReport
            The report to be used in the registration process.
        '''

# --------------------------------------------------------------------

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
        
        assert callable(definer), 'Invalid definer %s' % definer
        
        self = super().__new__(cls, *definer(name, bases, namespace))
        
        for name, attribute in self.__attributes__.items():
            assert isinstance(attribute, IAttribute)
            attribute.place(self, name)
        
        return self
    
    def __str__(self):
        return '<context \'%s.%s(%s)\'>' % (self.__module__, self.__name__, ', '.join(self.__attributes__))

# --------------------------------------------------------------------

def isNameForClass(name):
    '''
    Function used for determining if a context name is targeting a class rather then a value.
    
    @param name: string
        The name to check.
    @return: boolean
        True if the name represents a context class name by convention, False otherwise.
    '''
    assert isinstance(name, str), 'Invalid name %s' % name
    assert name, 'Invalid empty name'
    return name[:1].lower() != name[:1]
