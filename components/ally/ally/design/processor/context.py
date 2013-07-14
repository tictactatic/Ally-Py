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
        
        @param attribute: tuple(string, IAttribute) or descriptor with '__name__' and '__objclass__'
            The attribute to check if contained.
        '''
        if attribute is None: return False
        if not isinstance(attribute, IAttribute):
            try: name, clazz = attribute.__name__, attribute.__objclass__
            except AttributeError: return False
                
            if not isinstance(clazz, ContextMetaClass): return False
            assert isinstance(clazz, ContextMetaClass)
            attribute = clazz.__attributes__.get(name)
            
            if not isinstance(attribute, IAttribute): return False
            assert isinstance(attribute, IAttribute)
        
        return attribute.isIn(self.__class__)
    
    def __str__(self):
        '''
        Assigned to the context as the __str__ method.
        '''
        namesValues = ((name, getattr(self, name)) for name, attr in self.__attributes__.items() if attr in self)
        attrs = ', '.join('%s=%s' % (name, 'self' if value == self else value) for name, value in namesValues)
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

def asData(context, *classes):
    '''
    Provides the data that is represented in the provided context classes.
    
    @param context: object
        The context object to get the data from.
    @param classes: arguments[ContextMetaClass]
        The context classes to construct the data based on.
    '''
    assert isinstance(context, Context), 'Invalid context %s' % context

    common = set(context.__attributes__)
    for clazz in classes:
        assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        common.intersection_update(clazz.__attributes__)
        
    data = {}
    for name in common:
        if context.__attributes__[name] in context: data[name] = getattr(context, name)

    return data

def pushIn(dest, *srcs, interceptor=None, exclude=()):
    '''
    Pushes in the destination context data from the source context(s).
    
    @param dest: object
        The destination context object to get the data from.
    @param srcs: arguments[Context|dictionary{string: object}]
        Sources to copy data from, attention the order is important since if the first context has no value
        for an attribute then the second one is checked and so on.
    @param interceptor: callable(object) -> object|None
        An interceptor callable to be called before setting the value on the destination.
    @param exclude: tuple(string)|list[string]|set(string)
        The attributes to be excluded from the push.
    @return: object
        The destination context after copy.
    '''
    assert isinstance(dest, Object), 'Invalid destination context %s' % dest
    assert srcs, 'At least one source is required'
    assert interceptor is None or callable(interceptor), 'Invalid interceptor %s' % interceptor
    assert isinstance(exclude, (tuple, list, set)), 'Invalid exclude %s' % exclude
        
    for name in dest.__attributes__:
        if exclude and name in exclude: continue
        found = False
        for src in srcs:
            if isinstance(src, Context):
                attribute = src.__attributes__.get(name)
                if attribute and attribute in src: found, value = True, getattr(src, name)
            else:
                assert isinstance(src, dict), 'Invalid source %s' % src
                if name in src: found, value = True, src[name]
            
            if found:
                if interceptor is not None: value = interceptor(value)
                setattr(dest, name, value)
                break
    
    return dest

def cloneCollection(value):
    '''
    Interceptor to be used on the 'pushIn' function that creates new collections with the same items.
    The collections copied are: set, dict, list.
    
    @param value: object
        The value to intercept.
    @return: object
        The clone collection if is the case or the same value.
    '''
    if value is None: return
    clazz = value.__class__
    if clazz == set: return set(value)
    elif clazz == dict: return dict(value)
    elif clazz == list: return list(value)
    return value
