'''
Created on Jun 12, 2012

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the context support.
'''

from .spec import IAttribute, ContextMetaClass, CREATE_DEFINITION, IResolver
from ally.support.util import immut
from weakref import WeakSet

# --------------------------------------------------------------------

ALLOWED = {'__module__', '__doc__', '__locals__'}
# The allowed keys in the namespace.

# --------------------------------------------------------------------

def definerContext(name, bases, namespace):
    '''
    Process the provided context definition parameters.
        
    @param name: string
        The class name.
    @param bases: tuple(class)
        The inherited classes.
    @param namespace: dictionary{string, object}
        The context name space definition.
    @return: tuple(string, tuple(classes), dictionary{string, object})
        The name, basses and namespace to use in constructing the context class.
    '''
    assert isinstance(namespace, dict), 'Invalid namespace %s' % namespace
    assert isinstance(bases, tuple), 'Invalid bases %s' % bases
    assert bases, 'At least one base class is required'
    
    attributes = {}
    for key, value in namespace.items():
        if key in ALLOWED: continue
        if not isinstance(value, IAttribute):
            raise TypeError('Invalid attribute \'%s\' for name \'%s\'' % (value, key))
        attributes[key] = value
    
    # Adding also the parent attributes.
    for base in bases:
        if base is Context: continue
        if not isinstance(base, ContextMetaClass):
            raise TypeError('A context class can only inherit other context classes, invalid class %s' % base)
        assert isinstance(base, ContextMetaClass)
        if base.__definer__ != definerContext:
            raise TypeError('Cannot define because of inherited context class %s' % base)
        
        for key, attribute in base.__attributes__.items():
            if key not in attributes: attributes[key] = attribute
    
    namespace['__attributes__'] = immut(attributes)
    return name, bases, namespace
        
def definerObject(name, bases, namespace):
    '''
    Process the provided object definition parameters.
        
    @param name: string
        The class name.
    @param bases: tuple(class)
        The inherited classes.
    @param namespace: dictionary{string, object}
        The context name space definition.
    @return: tuple(string, tuple(classes), dictionary{string, object})
        The name, basses and namespace to use in constructing the context class.
    '''
    assert isinstance(namespace, dict), 'Invalid namespace %s' % namespace
    assert isinstance(bases, tuple), 'Invalid bases %s' % bases
    assert bases == (Object,), 'No bases are allowed for object contexts other then Object'
    assert '__attributes__' in namespace, 'No attributes defined for context object'
    
    namespace['__slots__'] = tuple(namespace['__attributes__'])
    return name, bases, namespace

# --------------------------------------------------------------------

class Context(metaclass=ContextMetaClass):
    '''
    The base context class, this class needs to be inherited by all classes that need to behave like a data context definition
    only, no objects for this contexts can be created.
    '''
    __definer__ = definerContext

    @classmethod
    def __subclasshook__(cls, C):
        '''
        Assigned to the context as the __subclasshook__ method.
        '''
        if not isinstance(cls, ContextMetaClass): return NotImplemented
        if not isinstance(C, ContextMetaClass): return False
        assert isinstance(cls, ContextMetaClass)
        
        for attribute in cls.__attributes__.values():
            assert isinstance(attribute, IAttribute)
            if not attribute.isValid(C): return False
        return True
    
    def __new__(cls, *args, **keyargs):
        '''
        Assigned to the context as the __new__ method in order to prevent creation.
        '''
        raise TypeError('Cannot create an instance for %s' % cls)
    
class Object(metaclass=ContextMetaClass):
    '''
    The base object context class, this class needs to be inherited by all classes that need to behave like a data context that
    can have object created.
    '''
    __definer__ = definerObject
    __subclasshook__ = Context.__subclasshook__
    
    _contained = WeakSet()
    _uncontained = WeakSet()
    
    def __init__(self, **keyargs):
        '''
        Assigned to the context as the __init__ method.
        '''
        for name, value in keyargs.items(): setattr(self, name, value)

    def __getattr__(self, name):
        '''
        Assigned to the context whenever the application is in not in debug mode and there is no need to perform validations.
        '''
        if name in self.__attributes__: return None
        raise AttributeError('Unknown attribute \'%s\'' % name)
    
    def __contains__(self, attribute):
        '''
        Assigned to the context as the __contains__ method.
        
        @param attribute: IAttribute or descriptor with '__name__' and '__objclass__'
            The attribute to check if contained.
        '''
        attribute = attributeOf(attribute)
        if attribute is None: return False
        if attribute in self.__class__._contained: return True
        if attribute in self.__class__._uncontained: return False
        assert isinstance(attribute, IAttribute)
        if attribute.isIn(self.__class__):
            self.__class__._contained.add(attribute)
            return True
        self.__class__._uncontained.add(attribute)
        return False
    
    def __str__(self):
        '''
        Assigned to the context as the __str__ method.
        '''
        namesValues = ((name, getattr(self, name)) for name, attr in self.__attributes__.items() if attr in self)
        attrs = ', '.join('%s=%s' % (name, 'Context' if isinstance(value, Context) else value)
                          for name, value in namesValues)
        return '%s(%s)' % (self.__class__.__name__, attrs)

# --------------------------------------------------------------------

def create(resolvers, *flags):
    '''
    Creates the object contexts for the provided resolvers.
    
    @param resolvers: dictionary{string: IResolver}
        The resolvers to create the context for.
    @param flags: arguments[object]
        Flags to be used for creating the attributes.
    @return: dictionary{string: ContextMetaClass}
        The created context classes.
    '''
    assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
    contexts = {}
    for name, resolver in resolvers.items():
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
        attributes = resolver.create(*flags)
        if not attributes: continue  # The resolver has no context to be created
        
        assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
        nameClass = '%s%s' % (name[0].upper(), name[1:])
        
        if CREATE_DEFINITION in flags:
            namespace = dict(__module__=__name__)
            namespace.update(attributes)
            contexts[name] = type('Context$%s' % nameClass, (Context,), namespace)
            
        else:
            namespace = dict(__module__=__name__, __attributes__=attributes)
            contexts[name] = type('Object$%s' % nameClass, (Object,), namespace)

    return contexts

def attributeOf(descriptor):
    '''
    Provides the @see: IAttribute for the provided descriptor or attribute.
    
    @param descriptor: object
        The descriptor to provide the attribute for.
    @return: IAttribute|None
        The attribute or None if the descriptor is invalid.
    '''
    if descriptor is None: return
    if isinstance(descriptor, IAttribute): return descriptor
    try: name, clazz = descriptor.__name__, descriptor.__objclass__
    except AttributeError: return
        
    if not isinstance(clazz, ContextMetaClass): return
    assert isinstance(clazz, ContextMetaClass)
    attribute = clazz.__attributes__.get(name)
    
    if isinstance(attribute, IAttribute): return attribute
