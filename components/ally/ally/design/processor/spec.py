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
    The attribute resolver specification.
    '''
    __slots__ = ()
    
    @abc.abstractmethod
    def push(self, name, resolvers):
        '''
        Pushes a resolver that reflects this resolver into the provided resolvers repository.
        
        @param name: string
            The context name to associate with the resolver.
        @param resolvers: IResolver
            The repository to push the resolver to.
        '''

    @abc.abstractmethod
    def merge(self, other, isFirst=True):
        '''
        Merges this attribute resolver with the other attribute resolver.
        
        @param other: IResolver
            The attribute resolver to merge with.
        @param isFirst: boolean
            Flag indicating that if this attribute resolver is the first one in the merging process, in many cases is very 
            important who gets merged with whom.
        @return: IResolver
            The attribute resolver obtained by combining this attribute resolver and the other attribute resolver.
        '''
        
    @abc.abstractmethod
    def solve(self, other):
        '''
        Solve this attribute resolver with the other attribute resolver. The solving it differs from merging because the 
        resolvers need to complete each other.
        
        @param other: IResolver
            The attribute resolver to solve with.
        @return: IResolver
            The attribute resolver obtained by solving this attribute resolver with the other attribute resolver.
        '''
    
    @abc.abstractmethod
    def isAvailable(self):
        '''
        Checks if there is an attribute available to generate.
        
        @return: boolean
            True if it can generate an attribute, False otherwise.
        '''
        
    @abc.abstractmethod
    def isUsed(self):
        '''
        Checks if the attribute resolver will generated a used attribute.
        
        @return: boolean
            True if the generated attribute is used, False otherwise.
        '''
    
    @abc.abstractmethod
    def create(self, attributes):
        '''
        Create the attributes to be used on a new object context. The 'isAvailable' method should be checked first.
        
        @param attributes: dictionary{string: IAttribute}
            The attributes dictionary where to place the resolver object attribute.
        '''
        
    @abc.abstractmethod
    def createDefinition(self, attributes):
        '''
        Create the attributes to be used on a new definition context.
        
        @param attributes: dictionary{string: IAttribute}
            The attributes dictionary where to place the resolver definition attribute.
        '''

class IResolvers(metaclass=abc.ABCMeta):
    '''
    Attributes resolvers repository specification.
    '''
    __slots__ = ()
    
    @abc.abstractmethod 
    def lock(self):
        '''
        Locks this resolvers repository.
        '''
    
    @abc.abstractmethod
    def add(self, name, attribute, resolver):
        '''
        Adds a new resolver to this repository.
        
        @param name: string
            The context name represented by the resolver.
        @param attribute: string
            The attribute name represented by the resolver.
        @param resolver: IResolver
            The resolver to add to the repository.
        '''
    
    @abc.abstractmethod  
    def merge(self, other, joined=True):
        '''
        Merges into this resolvers repository the provided resolvers or contexts.
        
        @param other: IResolvers|dictionary{string, ContextMetaClass)
            The resolvers or dictionary of context to merge with.
        @param joined: boolean
            If True then the other resolvers that are not found in this resolvers repository will be added, if False
            the merging is done only on existing resolvers in this repository.
        '''
    
    @abc.abstractmethod
    def solve(self, other, joined=True):
        '''
        Solves into this resolver repository the provided resolvers or contexts.
        
        @param other: IResolvers|dictionary{string, ContextMetaClass)
            The resolvers or dictionary of context to solve with.
        @param joined: boolean
            If True then the other resolvers that are not found in this resolvers repository will be added, if False
            the solving is done only on existing resolvers in this repository.
        '''
    
    # ----------------------------------------------------------------
    
    @abc.abstractmethod
    def copy(self, names=None):
        '''
        Creates a copy for this resolvers repository, if this repository has the locked flag it will no be passed on to the copy.
        
        @param names: Iterable(string|tuple(string, string))|None
            The context or attribute names to copy the resolvers for, if None then all resolvers are copied.
        @return: Resolvers
            The cloned resolvers repository.
        '''
    
    @abc.abstractmethod
    def extract(self, names):
        '''
        Extracts from this resolvers repository all the resolvers for the provided context or attribute names.
        
        @param names: Iterable(string|tuple(string, string))
            The context or attribute names to extract the resolvers for.
        @return: IResolvers
            The extracted resolvers repository.
        '''
    
    # ----------------------------------------------------------------

    @abc.abstractmethod
    def validate(self):
        '''
        Validates the resolvers in this repository.
        '''
    
    @abc.abstractmethod
    def iterateNames(self):
        '''
        Iterates the resolvers names for this resolvers repository.
        
        @return: Iterable(tuple(string, string))
            The resolvers names iterator.
        '''
    
    @abc.abstractmethod
    def iterate(self):
        '''
        Iterates the resolvers for this resolvers repository.
        
        @return: Iterable(tuple(string, string), IResolver)
            The resolvers iterator.
        '''

# --------------------------------------------------------------------
        
class IAttribute(metaclass=abc.ABCMeta):
    '''
    The attribute specification.
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
    def push(self, name, resolvers):
        '''
        Pushes a resolver for this attribute into the provided resolvers repository.
        
        @param name: string
            The context name to associate with the resolver.
        @param resolvers: Resolvers
            The repository to push the resolver to.
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
        
        @param resolvers: IResolver
            The resolvers repository to be reported.
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
        
        @param sources: IResolver
            The sources attributes resolvers that need to be solved by processors.
        @param resolvers: IResolver
            The attributes resolvers solved so far by processors.
        @param extensions: IResolver
            The attributes resolvers that are not part of the main stream resolvers but they are rather extension for the created
            contexts.
        @param calls: list[callable]
            The list of callable objects to register the processor call into.
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
