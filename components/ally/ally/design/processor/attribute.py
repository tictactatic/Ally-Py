'''
Created on Feb 11, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the attributes support.
'''

from .spec import IAttribute, AttrError, IResolver, ResolverError, \
    ContextMetaClass, LIST_UNAVAILABLE, LIST_UNUSED, CREATE_DEFINITION
from ally.design.processor.spec import LIST_CLASSES
from ally.support.util_spec import IGet, ISet
from ally.support.util_sys import locationStack
from collections import Iterable
from inspect import isclass
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

def defines(*types, doc=None):
    '''
    Construct a defining attribute for the context. The defines attribute means that the context can provide a value
    for the attribute, but is not mandatory also whenever managing an attribute if this type is a good idea to check
    if there aren't already values provided.
    
    @param types: arguments[class]
        The types of the defined attribute.
    @param doc: string|None
        The documentation associated with the attribute.
    '''
    return Attribute(Specification(DEFINED, types, doc=doc))

def definesIf(*types, doc=None):
    '''
    Construct a defining attribute for the context. The defines attribute means that the context can provide a value
    for the attribute, but is not mandatory also whenever managing an attribute if this type is a good idea to check
    if there aren't already values provided. Whenever using this type of attributes always check if the context has them since
    if they are optional they might not event be populated if there is no definition for them, so always to a check like:
        MyContext.myAttribute in myInstance
    , otherwise you might get attribute error.
    
    @param types: arguments[class]
        The types of the defined attribute.
    @param doc: string|None
        The documentation associated with the attribute.
    '''
    return Attribute(Specification(DEFINED | OPTIONAL, types, doc=doc))

def optional(*types, doc=None):
    '''
    Construct an optional attribute for the context. The optional attribute means that the context is valid even if
    there is no value for the attribute. Whenever using this type of attributes always check if the context has them since
    if they are optional they might not event be populated if there is no definition for them, so always to a check like:
        MyContext.myAttribute in myInstance
    , otherwise you might get attribute error.
    
    @param types: arguments[class]
        The types of the optional attribute, the attribute value can be any one of the provided attributes.
    @param doc: string|None
        The documentation associated with the attribute.
    '''
    return Attribute(Specification(OPTIONAL, types, doc))

def requires(*types, doc=None):
    '''
    Construct a required attribute for the context. The requires attribute means that the context is valid only if
    there is a value for the attribute.
    
    @param types: arguments[class]
        The types of the required attribute, the attribute value can be any one of the provided attributes.
    @param doc: string|None
        The documentation associated with the attribute.
    '''
    return Attribute(Specification(REQUIRED, types, doc=doc))

# --------------------------------------------------------------------

class Definition:
    '''
    Descriptor used just to provide the definition.
    '''
    __slots__ = ('__objclass__', '__name__')

    def __init__(self, clazz, name, types):
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

    def __init__(self, clazz, name, types):
        '''
        Construct the property.
        
        @param clazz: class
            The class of the descriptor.
        @param name: string
            The name of the attribute descriptor.
        @param types: tuple(class)
            The types to validate the values for.
        '''
        assert isclass(clazz), 'Invalid class %s' % clazz
        assert hasattr(clazz, name), 'Invalid class %s has no descriptor for %s' % (clazz, name)
        assert isinstance(types, tuple), 'Invalid types %s' % types
        assert types, 'At least a type is required'
        if __debug__:
            for typeClazz in types: assert isclass(typeClazz), 'Invalid type class %s' % typeClazz

        self.types = types
        self.descriptor = getattr(clazz, name)
        assert isinstance(self.descriptor, IGet), 'Invalid descriptor %s' % self.descriptor
        assert isinstance(self.descriptor, ISet), 'Invalid descriptor %s' % self.descriptor

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

class Resolver(IResolver):
    '''
    Implementation for a @see: IResolver that manages contexts with @see: Attribute.
    '''
    __slots__ = ('specifications',)

    def __init__(self, context):
        '''
        Construct the attribute resolver.
        
        @param context: ContextMetaClass|dictionary{string: Specification}
            The context class to construct the resolver based on, or the specifications dictionary.
        '''
        if isinstance(context, ContextMetaClass):
            assert isinstance(context, ContextMetaClass)
            specifications = {}
            for name, attribute in context.__attributes__.items():
                assert isinstance(name, str), 'Invalid name %s' % name
                assert isinstance(attribute, Attribute), 'Invalid attribute %s' % attribute
                specifications[name] = attribute.specification
                
        else:
            assert isinstance(context, dict), 'Invalid context %s' % context
            if __debug__:
                for name, spec in context.items():
                    assert isinstance(name, str), 'Invalid name %s' % name
                    assert isinstance(spec, Specification), 'Invalid specification %s' % spec
            specifications = context
            
        self.specifications = specifications
        
    def copy(self, names=None):
        '''
        @see: IResolver.copy
        '''
        specifications = {}
        if names is None:
            specifications.update(self.specifications)
            
        else:
            assert isinstance(names, Iterable), 'Invalid names %s' % names
            for name in names:
                assert isinstance(name, str), 'Invalid name %s' % name
                spec = self.specifications.get(name)
                if spec: specifications[name] = spec
                    
        return Resolver(specifications)
            
    def merge(self, other, isFirst=True):
        '''
        @see: IResolver.merge
        '''
        assert isinstance(other, IResolver), 'Invalid other resolver %s' % other
        assert isinstance(isFirst, bool), 'Invalid is first flag %s' % isFirst
        
        if self is other: return self
        
        if not other.__class__ == Resolver:
            if isFirst: return other.merge(self, False)
            raise ResolverError('Cannot merge %s with %s' % (self, other))
        assert isinstance(other, Resolver), 'Invalid other resolver %s' % other
        
        specifications = dict(self.specifications)
        for name, spec in other.specifications.items():
            ownSpec = specifications.get(name)
            if ownSpec is None: specifications[name] = spec
            else:
                try: specifications[name] = self.mergeSpecifications(ownSpec, spec)
                except AttrError:
                    raise AttrError('Cannot merge attribute \'%s\', from:%s\n, with:%s' % 
                                    (name, ''.join(locationStack(clazz) for clazz in ownSpec.usedIn),
                                     ''.join(locationStack(clazz) for clazz in spec.usedIn)))
        
        return Resolver(specifications)
    
    def solve(self, other):
        '''
        @see: IResolver.solve
        '''
        assert isinstance(other, IResolver), 'Invalid other resolver %s' % other
        if self is other: return self
        
        if not other.__class__ == Resolver: return other.solve(self)
        assert isinstance(other, Resolver), 'Invalid other resolver %s' % other
        
        specifications = dict(self.specifications)
        for name, spec in other.specifications.items():
            assert isinstance(spec, Specification), 'Invalid specification %s' % spec
            ownSpec = specifications.get(name)
            if ownSpec is None: specifications[name] = spec
            elif ownSpec.status & DEFINED: specifications[name] = self.mergeSpecifications(ownSpec, spec)
            else: specifications[name] = self.mergeSpecifications(spec, ownSpec)
        
        return Resolver(specifications)
    
    def list(self, *flags):
        '''
        @see: IResolver.list
        '''
        flags, attributes = set(flags), {}
        
        listed = False
        try: flags.remove(LIST_UNAVAILABLE)
        except KeyError: pass
        else:
            listed = True
            for name, spec in self.specifications.items():
                assert isinstance(spec, Specification), 'Invalid specification %s' % spec
                if spec.status == REQUIRED: attributes[name] = None
                
        try: flags.remove(LIST_UNUSED)
        except KeyError: pass
        else:
            listed = True
            for name, spec in self.specifications.items():
                assert isinstance(spec, Specification), 'Invalid specification %s' % spec
                if not spec.status & OPTIONAL:
                    if len(spec.usedIn) <= 1:
                        attributes[name] = None
                    else:
                        for status in spec.usedIn.values():
                            if not status & DEFINED: break
                        else: attributes[name] = None
                
        if not listed:
            for name in self.specifications: attributes[name] = None
            
        try: flags.remove(LIST_CLASSES)
        except KeyError: pass
        else:
            for name in attributes: attributes[name] = self.specifications[name].usedIn.keys()
        
        assert not flags, 'Unknown flags: %s' % ', '.join(flags)
        return attributes
            
    def create(self, *flags):
        '''
        @see: IResolver.create
        '''
        flags, attributes = set(flags), {}
        
        created = False
        try: flags.remove(CREATE_DEFINITION)
        except KeyError: pass
        else:
            created = True
            for name, spec in self.specifications.items():
                assert isinstance(spec, Specification), 'Invalid specification %s' % spec
                attributes[name] = Attribute(spec)
        
        if not created:
            for name, spec in self.specifications.items():
                assert isinstance(spec, Specification), 'Invalid specification %s' % spec
                if spec.status == REQUIRED:
                    raise AttrError('Cannot generate attribute %s=%s, used in:%s' % 
                                    (name, spec, ''.join(locationStack(clazz) for clazz in spec.usedIn)))
                if spec.status & OPTIONAL: continue  # If is optional then no need to create it
                attributes[name] = Attribute(spec, Descriptor=Descriptor)
            
        assert not flags, 'Unknown flags: %s' % ', '.join(flags)
        return attributes
                
    # ----------------------------------------------------------------
    
    def mergeSpecifications(self, mergeSpec, withSpec):
        '''
        Merges the provided specifications.
        
        @param mergeSpec: Specification
            The specification to be merged.
        @param withSpec: Specification
            The specification to merge with.
        '''
        assert isinstance(mergeSpec, Specification), 'Invalid merge specification %s' % mergeSpec
        assert isinstance(withSpec, Specification), 'Invalid with specification %s' % withSpec
        
        if mergeSpec is withSpec: return mergeSpec

        if mergeSpec.status == REQUIRED:
            if withSpec.status & DEFINED:
                raise AttrError('Improper order for %s, it should be before %s' % (withSpec, mergeSpec))
            status = REQUIRED
            types = set(mergeSpec.types)
            types.intersection_update(withSpec.types)
            if not types:
                raise AttrError('Incompatible required types of %s, with required types of %s' % (mergeSpec, withSpec))
                
        elif mergeSpec.status == OPTIONAL:
            if withSpec.status & DEFINED:
                status = DEFINED
                types = set(mergeSpec.types)
            else:
                status = withSpec.status
                types = set(mergeSpec.types)
                types.intersection_update(withSpec.types)
                if not types:
                    raise AttrError('Incompatible required types of %s, with required types of %s' % (mergeSpec, withSpec))
            
        elif mergeSpec.status & DEFINED:
            status = DEFINED
            if withSpec.status & DEFINED: 
                types = set(mergeSpec.types)
                types.update(withSpec.types)
                # In case both definitions are optional we need to relate that to the merged attribute
                if mergeSpec.status & OPTIONAL and withSpec.status & OPTIONAL: status |= OPTIONAL
            else:
                types = set(withSpec.types)
                
        defined = set(mergeSpec.defined)
        defined.update(withSpec.defined)
        if defined != types and not types.issuperset(defined):
            raise ResolverError('Invalid types %s and defined types %s, they cannot be joined, for %s, and %s' % 
                                (', '.join('\'%s\'' % typ.__name__ for typ in types),
                                 ', '.join('\'%s\'' % typ.__name__ for typ in defined), mergeSpec, withSpec))
        
        docs = []
        if mergeSpec.doc is not None: docs.append(mergeSpec.doc)
        if withSpec.doc is not None: docs.append(withSpec.doc)
        doc = '\n'.join(docs) if docs else None
        spec = Specification(status, tuple(types), doc, defined)
        spec.usedIn.update(mergeSpec.usedIn)
        spec.usedIn.update(withSpec.usedIn)
        
        return spec
    
    def __str__(self):
        if not self.specifications: return '%s empty' % self.__class__.__name__
        return '%s[%s]' % (self.__class__.__name__, ', '.join('%s=%s' % (name, self.specifications.get(name))
                                                              for name in sorted(self.specifications)))

# --------------------------------------------------------------------

DEFINED = 1 << 1
# Status flag for defined attributes.
REQUIRED = 1 << 2
# Status flag for required attributes.
OPTIONAL = 1 << 3
# Status flag for optional attributes.

class Specification:
    '''
    Provides attribute specifications.
    '''
    __slots__ = ('status', 'types', 'doc', 'defined', 'usedIn')
    
    def __init__(self, status, types, doc=None, defined=None):
        '''
        Construct the attribute specification.
        
        @param status: integer
            The status of the attribute.
        @param types: tuple(class)
            The type(s) for the attribute.
        @param doc: string|None
            The documentation associated with the attribute.
        @param defined: Iterable(class)|None
            The defined classes.
        '''
        assert isinstance(status, int), 'Invalid status %s' % status
        assert isinstance(types, tuple), 'Invalid types %s' % types
        assert types, 'At least a type is required'
        if __debug__:
            for clazz in types: assert isclass(clazz), 'Invalid class %s' % clazz
        
        if defined is None:
            if status & DEFINED: defined = types
            else: defined = ()
        else: assert isinstance(defined, Iterable), 'Invalid defined classes %s' % defined
        
        self.status = status
        self.types = types
        self.doc = doc
        self.defined = frozenset(defined)
        
        self.usedIn = {}
        
    def __str__(self):
        status = []
        if self.status & DEFINED: status.append('DEFINES')
        if self.status & REQUIRED: status.append('REQUIRED')
        if self.status & OPTIONAL: status.append('OPTIONAL')
        
        return ''.join(('|'.join(status), '[', ','.join(t.__name__ for t in self.types), ']'))

class Attribute(IAttribute):
    '''
    Implementation for a @see: IAttribute that manages a attributes by status.
    '''
    __slots__ = ('specification', 'Resolver', 'Descriptor', 'clazz', 'name')

    def __init__(self, specification, Resolver=Resolver, Descriptor=Definition):
        '''
        Construct the attribute.
        
        @param specification: Specification
            The attribute specification.
        @param Resolver: class
            The resolver class for the attribute.
        @param Descriptor: callable(class, string, tuple(class)) -> object
            The descriptor factory to use in creating the descriptors for the place command.
            The factory receives the class the attribute name and the types.
        '''
        assert isinstance(specification, Specification), 'Invalid specification %s' % specification
        assert isclass(Resolver), 'Invalid resolver class %s' % Resolver
        assert callable(Descriptor), 'Invalid descriptor factory %s' % Descriptor
        
        self.specification = specification
        self.Resolver = Resolver
        self.Descriptor = Descriptor
        
        self.clazz = None
        self.name = None
    
    def resolver(self):
        '''
        @see: IAttribute.resolver
        '''
        return self.Resolver
    
    def place(self, clazz, name):
        '''
        @see: IAttribute.place
        '''
        if self.clazz is None:
            assert isinstance(clazz, ContextMetaClass), 'Invalid class %s' % clazz
            assert isinstance(name, str), 'Invalid name %s' % name
            
            setattr(clazz, name, self.Descriptor(clazz, name, self.specification.types))
            self.clazz, self.name = clazz, name
            self.specification.usedIn[clazz] = self.specification.status
        elif not issubclass(clazz, self.clazz) or self.name != name:
            raise AttrError('%s\n, is already placed in:%s as attribute %s' % (self, locationStack(self.clazz), self.name))
        
    def isValid(self, clazz):
        '''
        @see: IAttribute.isValid
        '''
        if not self.clazz: return False
        assert isclass(clazz), 'Invalid class %s' % clazz
        
        if not isinstance(clazz, ContextMetaClass): return False
        assert isinstance(clazz, ContextMetaClass)
        
        other = clazz.__attributes__.get(self.name)
        if other is None:
            if self.specification.status != REQUIRED: return True
            return False
        
        if not isinstance(other, Attribute): return False
        assert isinstance(other, Attribute)
        
        for typ in self.specification.types:
            if typ in other.specification.types: break
        else: return False
        
        return True
    
    def isIn(self, clazz):
        '''
        @see: IAttribute.isIn
        '''
        if not self.clazz: return False
        assert isclass(clazz), 'Invalid class %s' % clazz
        
        if not isinstance(clazz, ContextMetaClass): return False
        assert isinstance(clazz, ContextMetaClass)
        
        other = clazz.__attributes__.get(self.name)
        if other is None: return False
        
        if not isinstance(other, Attribute): return False
        assert isinstance(other, Attribute)
        
        for typ in self.specification.types:
            if typ in other.specification.types: break
        else: return False
        
        return True
    
    def __str__(self):
        st = ''.join((self.__class__.__name__, '.', str(self.specification)))
        if self.clazz:
            return ''.join((st, ' in:', locationStack(self.clazz), ' as attribute ', self.name))
        return ''.join((st, ' unplaced'))
