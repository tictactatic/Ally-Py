'''
Created on Feb 11, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the attributes support.
'''

from .spec import IAttribute, AttrError, ContextMetaClass
from ally.support.util_sys import locationStack
from inspect import isclass
from collections import Iterable

# --------------------------------------------------------------------

def defines(*types, doc=None):
    '''
    Construct a defining attribute for the context. The defines attribute means that the context can provide a value
    for the attribute, but is not mandatory also whenever managing an attribute if this type is a good idea to check
    if there aren't already values provided.
    
    @param types: arguments[class]
        The types of the defined attribute.
    @keyword doc: string
        The documentation associated with the attribute.
    '''
    return Attribute(DEFINED, types, doc=doc)

def optional(*types, doc=None):
    '''
    Construct an optional attribute for the context. The optional attribute means that the context is valid even if
    there is no value for the attribute.
    
    @param types: arguments[class]
        The types of the optional attribute, the attribute value can be any one of the provided attributes.
    @keyword doc: string
        The documentation associated with the attribute.
    '''
    return Attribute(OPTIONAL, types, doc)

def requires(*types, doc=None):
    '''
    Construct a required attribute for the context. The requires attribute means that the context is valid only if
    there is a value for the attribute.
    
    @param types: arguments[class]
        The types of the required attribute, the attribute value can be any one of the provided attributes.
    @param doc: string
        The documentation associated with the attribute.
    '''
    return Attribute(REQUIRED, types, doc=doc)

# --------------------------------------------------------------------

DEFINED = 1 << 1
# Status flag for defined attributes.
REQUIRED = 1 << 2
# Status flag for required attributes.
OPTIONAL = 1 << 3
# Status flag for optional attributes.

class Attribute(IAttribute):
    '''
    Implementation for a @see: IAttribute that manages a attributes by status.
    '''
    __slots__ = ('status', 'doc', 'defined', 'usedIn')

    def __init__(self, status, types, doc=None, defined=None):
        '''
        Construct the attribute.
        
        @param status: integer
            The status of the property.
        @param types: tuple(class)
            The type for the property.
        @param doc: string|None
            The documentation associated with the attribute.
        @param defined: Iterable(class)|None
            The defined classes.
        '''
        assert status in (DEFINED, OPTIONAL, REQUIRED), 'Invalid status %s' % status
        assert isinstance(types, tuple), 'Invalid types %s' % types
        assert types, 'At least a type is required'
        if __debug__:
            for clazz in types: assert isclass(clazz), 'Invalid class %s' % clazz
        
        if defined is None:
            if status == DEFINED: defined = types
            else: defined = ()
        else: assert isinstance(defined, Iterable), 'Invalid defined classes %s' % defined

        self.status = status
        self.types = types
        self.doc = doc
        self.defined = frozenset(defined)
        self.usedIn = {}
        
    def merge(self, other, isFirst=True):
        '''
        @see: IAttribute.merge
        '''
        assert isinstance(other, IAttribute), 'Invalid other attribute %s' % other
        assert isinstance(isFirst, bool), 'Invalid is first flag %s' % isFirst
        
        if self is other: return self
        
        if not isinstance(other, Attribute):
            if isFirst: return other.merge(self, False)
            raise AttrError('Cannot merge %s with %s' % (self, other))
        assert isFirst, 'Is required to be first for merging'
        assert isinstance(other, Attribute)
        
        if self.status == REQUIRED:
            if isFirst and other.status == DEFINED:
                raise AttrError('Improper order for %s, it should be before %s' % (other, self))
            status = REQUIRED
            types = set(self.types)
            types.intersection_update(other.types)
            if not types: raise AttrError('Incompatible required types of %s, with required types of %s' % (self, other))
                
        elif self.status == OPTIONAL:
            status = other.status
            if status == DEFINED: types = set(self.types)
            else: 
                types = set(self.types)
                types.intersection_update(other.types)
                if not types: raise AttrError('Incompatible required types of %s, with required types of %s' % (self, other))
            
        elif self.status == DEFINED:
            status = DEFINED
            if other.status == DEFINED: 
                types = set(self.types)
                types.update(other.types)
            else:
                types = set(other.types)
                
        defined = set(self.defined)
        defined.update(other.defined)
        if defined != types and not types.issuperset(defined):
            raise AttrError('Invalid types %s and defined types %s, they cannot be joined, for %s, and %s' % 
                            (', '.join('\'%s\'' % typ.__name__ for typ in types),
                             ', '.join('\'%s\'' % typ.__name__ for typ in defined), self, other))
        
        docs = []
        if self.doc is not None: docs.append(self.doc)
        if other.doc is not None: docs.append(other.doc)
        attribute = Attribute(status, tuple(types), '\n'.join(docs) if docs else None, defined)
        attribute.usedIn.update(self.usedIn)
        attribute.usedIn.update(other.usedIn)
        
        return attribute
    
    def solve(self, other):
        '''
        @see: IAttribute.solve
        '''
        assert isinstance(other, IAttribute), 'Invalid other attribute %s' % other
        
        if self is other: return self
        
        if self.status == DEFINED: attribute = self.merge(other, True)
        else: attribute = other.merge(self, True)
            
        return attribute
    
    def isCreatable(self):
        '''
        @see: IAttribute.isCreatable
        '''
        return self.status != REQUIRED
    
    def place(self, clazz, name, asDefinition):
        '''
        @see: IAttribute.place
        '''
        assert isinstance(clazz, ContextMetaClass), 'Invalid class %s' % clazz
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(asDefinition, bool), 'Invalid as definition flag %s' % asDefinition
        assert (clazz, name) not in self.usedIn, 'Already placed on class %s as \'%s\'' % (clazz, name)
        
        if asDefinition:
            setattr(clazz, name, Definition(clazz, name))
            for sclazz in clazz.mro():
                if (sclazz, name) in self.usedIn: break
            else:
                self.usedIn[(clazz, name)] = self.status
        else:
            if self.status == REQUIRED: raise AttrError('Cannot use for objects %s' % self)
            assert hasattr(clazz, name), 'Invalid class %s has no descriptor for %s' % (clazz, name)
            if __debug__: setattr(clazz, name, Descriptor(getattr(clazz, name), self.types))
        
    def isAvailable(self, clazz, name):
        '''
        @see: IAttribute.isAvailable
        '''
        assert isclass(clazz), 'Invalid class %s' % clazz
        assert isinstance(name, str), 'Invalid name %s' % name
        
        if not isinstance(clazz, ContextMetaClass): return False
        assert isinstance(clazz, ContextMetaClass)
        
        other = clazz.__attributes__.get(name)
        if other is None:
            if self.status != REQUIRED: return True
            return False
        
        if not isinstance(other, Attribute): return False
        assert isinstance(other, Attribute)
        
        for typ in self.types:
            if typ in other.types: break
        else: return False
        
        return True
        
    def isValid(self, value):
        '''
        @see: IAttribute.isValid
        '''
        if value is None: return False
        return isinstance(value, self.types)
    
    def isUsed(self):
        '''
        @see: IAttribute.isUsed
        '''
        return len(self.usedIn) > 1

    def __str__(self):
        status = None
        if self.status & DEFINED: status = 'DEFINES'
        if self.status & REQUIRED: status = 'REQUIRED'
        if self.status & OPTIONAL: status = 'OPTIONAL'
        st = ''.join((status, '[', ','.join(t.__name__ for t in self.types), ']'))
        st = ''.join((self.__class__.__name__, ' having ', st))
        
        if self.usedIn:
            used = (clazzName for clazzName, status in self.usedIn.items() if status == self.status)
            used = ['%s as attribute \'%s\'' % (locationStack(clazz), name) for clazz, name in used]
            return ''.join((st, ' used in:', ''.join(used), '\n'))
        return ''.join((st, ' unused'))

# --------------------------------------------------------------------

class Definition:
    '''
    Descriptor used just to provide the definition.
    '''
    __slots__ = ('__objclass__', '__name__')

    def __init__(self, clazz, name):
        '''
        Construct the definition.
        
        @param clazz: class
            The class of the definition.
        @param name: string
            The name of the attribute definition.
        '''
        assert isinstance(clazz, ContextMetaClass), 'Invalid class %s' % clazz
        assert isinstance(name, str), 'Invalid name %s' % name
        self.__objclass__ = clazz
        self.__name__ = name

    def __get__(self, obj, owner=None):
        '''
        Descriptor get.
        '''
        if obj is not None: raise TypeError('Operation not allowed')
        assert owner is None or owner == self.__objclass__, 'Invalid owner class %s expected %s' % (owner, self.__objclass__) 
        return self

    def __set__(self, obj, value):
        '''
        Descriptor set.
        '''
        raise TypeError('Operation not allowed')
        
class Descriptor:
    '''
    Descriptor used by the attribute in order to validate values.
    '''
    __slots__ = ('descriptor', 'types')

    def __init__(self, descriptor, types):
        '''
        Construct the property.
        
        @param descriptor: object type descriptor
            The descriptor to use to set the actual value on the instance.
        @param types: tuple(class)
            The types to validate the values for.
        '''
        assert descriptor is not None, 'A descriptor is required'
        assert hasattr(descriptor, '__get__'), 'Invalid descriptor %s has no __get__ method' % descriptor
        assert hasattr(descriptor, '__set__'), 'Invalid descriptor %s has no __set__ method' % descriptor
        assert isinstance(types, tuple), 'Invalid types %s' % types
        assert types, 'At least a type is required'
        if __debug__:
            for clazz in types: assert isclass(clazz), 'Invalid class %s' % clazz

        self.descriptor = descriptor
        self.types = types

    def __get__(self, obj, owner=None):
        '''
        Descriptor get.
        '''
        if obj is None: return self
        try: return self.descriptor.__get__(obj, owner)
        except AttributeError: return None

    def __set__(self, obj, value):
        '''
        Descriptor set.
        '''
        assert value is None or isinstance(value, self.types), 'Invalid value \'%s\' for %s' % (value, self.types)
        self.descriptor.__set__(obj, value)
