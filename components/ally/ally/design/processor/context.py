'''
Created on Jun 12, 2012

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the context support.
'''

from .spec import IAttribute, IDefiner, ContextMetaClass, Attributes
from ally.support.util import immut

# --------------------------------------------------------------------

class DefinerDefinition(IDefiner):
    '''
    Standard implementation for @see: IDefiner
    '''
    
    def __init__(self, allowed):
        '''
        Construct the standard definer.
        
        @param allowed: set(string)
            The allowed keys in the namespace.
        '''
        assert isinstance(allowed, set), 'Invalid allowed names %s' % allowed
        if __debug__:
            for name in allowed: assert isinstance(name, str), 'Invalid allowed name %s' % name
        self.allowed = allowed
        
    def process(self, name, bases, namespace):
        '''
        @see: IDefiner.process
        '''
        assert isinstance(namespace, dict), 'Invalid namespace %s' % namespace
        assert isinstance(bases, tuple), 'Invalid bases %s' % bases
        assert bases, 'At least one base class is required'
        
        attributes = self.attributesFor(namespace)
        for key in attributes: namespace.pop(key)
        
        # Adding also the parent attributes.
        for base in bases:
            if base is Context: continue
            if not isinstance(base, ContextMetaClass):
                raise TypeError('A context class can only inherit other context classes, invalid class %s' % base)
            assert isinstance(base, ContextMetaClass)
            if base.__definer__ != self:
                raise TypeError('Cannot define because of inherited context class %s' % base)
            
            for key, attribute in base.__attributes__.items():
                if key not in attributes: attributes[key] = attribute
        
        namespace['__attributes__'] = immut(attributes)
        return name, bases, namespace
        
    def finalize(self, clazz):
        '''
        @see: IDefiner.finalize
        '''
        assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        for name, attribute in clazz.__attributes__.items():
            assert isinstance(attribute, IAttribute)
            attribute.place(clazz, name, True)
            
    # ----------------------------------------------------------------
    
    def attributesFor(self, namespace):
        '''
        Extracts the attributes from name space.
        '''
        attributes = {}
        for key, value in namespace.items():
            if key in self.allowed: continue
            if not isinstance(value, IAttribute):
                raise TypeError('Invalid attribute \'%s\' for name \'%s\'' % (value, key))
            attributes[key] = value
        return attributes
            
class DefinerObject(DefinerDefinition):
    '''
    Object definer implementation for @see: IDefiner
    '''
        
    def process(self, name, bases, namespace):
        '''
        @see: IDefiner.process
        '''
        assert isinstance(namespace, dict), 'Invalid namespace %s' % namespace
        assert isinstance(bases, tuple), 'Invalid bases %s' % bases
        assert bases == (Object,), 'No bases are allowed for object contexts other then Object'
        
        attributes = self.attributesFor(namespace)
        for key in attributes: namespace.pop(key)
        namespace['__slots__'] = tuple(attributes)
        namespace['__attributes__'] = immut(attributes)
        return name, bases, namespace
        
    def finalize(self, clazz):
        '''
        @see: IDefiner.finalize
        '''
        assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        for name, attribute in clazz.__attributes__.items():
            assert isinstance(attribute, IAttribute)
            attribute.place(clazz, name, False)

# --------------------------------------------------------------------

class Context(metaclass=ContextMetaClass):
    '''
    The base context class, this class needs to be inherited by all classes that need to behave like a data context definition
    only, no objects for this contexts can be created.
    '''
    __definer__ = DefinerDefinition({'__module__', '__doc__', '__locals__'})

    @classmethod
    def __subclasshook__(cls, C):
        '''
        Assigned to the context as the __subclasshook__ method.
        '''
        if not isinstance(cls, ContextMetaClass): return NotImplemented
        if not isinstance(C, ContextMetaClass): return False
        assert isinstance(cls, ContextMetaClass)
        
        for name, attribute in cls.__attributes__.items():
            assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
            if not attribute.isAvailable(C, name): return False
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
    __definer__ = DefinerObject({'__module__', '__doc__', '__locals__'})
    
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
        if isinstance(attribute, tuple) and len(attribute) == 2:
            name, attribute = attribute
            if not isinstance(name, str): return False
        else:
            try: name, clazz = attribute.__name__, attribute.__objclass__
            except AttributeError: return False
            
            if not isinstance(clazz, ContextMetaClass): return False
            assert isinstance(clazz, ContextMetaClass)
            attribute = clazz.__attributes__.get(name)
        
        if not isinstance(attribute, IAttribute): return False
        assert isinstance(attribute, IAttribute)
        
        try: desc = getattr(self.__class__, name)
        except AttributeError: return False
        try: value = desc.__get__(self)
        except AttributeError: return False
        
        return attribute.isValid(value)
    
    def __str__(self):
        '''
        Assigned to the context as the __str__ method.
        '''
        namesValues = ((item[0], getattr(self, item[0])) for item in self.__attributes__.items() if item in self)
        attrs = ', '.join('%s=%s' % nameValue for nameValue in namesValues)
        return '%s(%s)' % (self.__class__.__name__, attrs)

# --------------------------------------------------------------------

def create(attributes):
    '''
    Creates the object contexts for the provided attributes.
    
    @param attributes: Attributes
        The attributes to create the context for.
    '''
    assert isinstance(attributes, Attributes), 'Invalid attributes %s' % attributes
    attributes.validate()
    
    namespaces = {}
    for key, attribute in attributes.iterate():
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        nameContext, nameAttribute = key

        namespace = namespaces.get(nameContext)
        if namespace is None: namespace = namespaces[nameContext] = dict(__module__=__name__)
        namespace[nameAttribute] = attribute

    return {name: type('Object$%s%s' % (name[0].upper(), name[1:]), (Object,), namespace)
            for name, namespace in namespaces.items()}

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
        if (name, context.__attributes__[name]) in context: data[name] = getattr(context, name)

    return data

def copy(src, dest, *classes):
    '''
    Copies the data from the source context to the destination context based on the provided context classes.
    
    @param context: object
        The context object to get the data from.
    @param classes: arguments[ContextMetaClass]
        The context classes to construct the data based on.
    '''
    assert isinstance(src, Context), 'Invalid source context %s' % src
    assert isinstance(dest, Context), 'Invalid destination context %s' % dest

    common = set(src.__attributes__)
    common.intersection_update(dest.__attributes__)
    for clazz in classes:
        assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        common.intersection_update(clazz.__attributes__)
        
    for name in common:
        if (name, src.__attributes__[name]) in src: setattr(dest, name, getattr(src, name))
