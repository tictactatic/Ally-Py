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
    return Attribute(Specification(OPTIONAL, types, doc=doc))

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

def attribute(*types, doc=None):
    '''
    Construct a simple attribute for the context that will be used by the processor that define it and is also available
    as a defined attribute.
    
    @param types: arguments[class]
        The types of the defined attribute.
    @param doc: string|None
        The documentation associated with the attribute.
    '''
    return Attribute(Specification(DEFINED | USED, types, doc=doc))

# --------------------------------------------------------------------

DEFINED = 1 << 1
# Status flag for defined attributes.
REQUIRED = 1 << 2
# Status flag for required attributes.
OPTIONAL = 1 << 3
# Status flag for optional attributes.
USED = 1 << 4
# Status flag for attributes that should be considered always used.

# --------------------------------------------------------------------

class Specification:
    '''
    Provides attribute specifications.
    '''
    __slots__ = ('status', 'types', 'definedIn', 'doc', 'defined', 'usedIn')
    
    def __init__(self, status, types, definedIn=None, doc=None, defined=None):
        '''
        Construct the attribute specification.
        
        @param status: integer
            The status of the attribute specification.
        @param types: Iterable(class)
            The type(s) for the attribute specification.
        @param definedIn: class|None
            The class that defines the specification, this is just in case the specification was created based on a definer.
        @param doc: string|None
            The documentation associated with the attribute specification.
        @param defined: Iterable(class)|None
            The defined classes.
        '''
        assert isinstance(status, int), 'Invalid status %s' % status
        types = tuple(reduce(types))
        assert types, 'At least a type is required'
        assert definedIn is None or isclass(definedIn), 'Invalid defined in %s' % definedIn
        
        if defined is None:
            if status & DEFINED: defined = types
            else: defined = ()
        else: assert isinstance(defined, Iterable), 'Invalid defined classes %s' % defined
        
        self.status = status
        self.types = types
        self.definedIn = definedIn
        self.doc = doc
        self.defined = frozenset(defined)
        
        self.usedIn = {}
        
    def __str__(self):
        status = []
        if self.status & DEFINED: status.append('DEFINES')
        if self.status & REQUIRED: status.append('REQUIRED')
        if self.status & OPTIONAL: status.append('OPTIONAL')
        
        return ''.join(('|'.join(status), '[', ','.join(t.__name__ for t in self.types), ']'))

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
                    
        return self.__class__(specifications)
            
    def merge(self, other, isFirst=True):
        '''
        @see: IResolver.merge
        '''
        assert isinstance(other, IResolver), 'Invalid other resolver %s' % other
        assert isinstance(isFirst, bool), 'Invalid is first flag %s' % isFirst
        
        if self is other: return self
        
        if not issubclass(self.__class__, other.__class__):
            if isFirst: return other.merge(self, False)
            raise ResolverError('Cannot merge %s with %s' % (self, other))
        assert isinstance(other, Resolver), 'Invalid other resolver %s' % other
        
        return self.__class__(self.mergeSpecifications(self.specifications, other.specifications))
    
    def solve(self, other):
        '''
        @see: IResolver.solve
        '''
        assert isinstance(other, IResolver), 'Invalid other resolver %s' % other
        if self is other: return self
        
        if not issubclass(self.__class__, other.__class__): return other.solve(self)
        assert isinstance(other, Resolver), 'Invalid other resolver %s' % other
        
        return self.__class__(self.solveSpecifications(self.specifications, other.specifications))
    
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
                
        try: flags.remove(LIST_CLASSES)
        except KeyError: listClasses = False
        else: listClasses = True
                
        try: flags.remove(LIST_UNUSED)
        except KeyError: pass
        else:
            listed = True
            for name, spec in self.specifications.items():
                assert isinstance(spec, Specification), 'Invalid specification %s' % spec
                if spec.status & USED: continue
                if spec.status & OPTIONAL: continue
                for status in spec.usedIn.values():
                    if not status & DEFINED:
                        if spec.definedIn is not None: attributes[name] = (spec.definedIn,) if listClasses else None
                        break
                else: attributes[name] = spec.usedIn.keys() if listClasses else None
            listClasses = False
                
        if not listed:
            for name in self.specifications: attributes[name] = None
            
        if listClasses:
            for name in attributes: attributes[name] = self.specifications[name].usedIn.keys()
        
        assert not flags, 'Unknown flags: %s' % ', '.join(flags)
        return attributes
            
    def create(self, *flags):
        '''
        @see: IResolver.create
        '''
        flags = set(flags)
        
        attributes = {}
        try: flags.remove(CREATE_DEFINITION)
        except KeyError:
            attributes = self.createDescriptors(self.specifications)
        else:
            attributes = self.createDefinitions(self.specifications)

        assert not flags, 'Unknown flags: %s' % ', '.join(flags)
        return attributes
                
    # ----------------------------------------------------------------
    
    def mergeSpecification(self, mergeSpec, withSpec, **keyargs):
        '''
        Merges the provided specifications.
        
        @param mergeSpec: Specification
            The specification to be merged.
        @param withSpec: Specification
            The specification to merge with.
        @param keyargs: key arguments
            Additional key arguments to be used in constructing the merged specification.
        @return: Specification
            The merged specification.
        '''
        assert isinstance(mergeSpec, Specification), 'Invalid merge specification %s' % mergeSpec
        assert isinstance(withSpec, Specification), 'Invalid with specification %s' % withSpec
        
        if mergeSpec is withSpec: return mergeSpec

        if mergeSpec.status == REQUIRED:
            if withSpec.status & DEFINED:
                raise AttrError('Improper order for %s, it should be before %s' % (withSpec, mergeSpec))
            status = REQUIRED
            types = intersect(mergeSpec.types, withSpec.types)
            if not types:
                raise AttrError('Incompatible required types of %s, with required types of %s' % (mergeSpec, withSpec))
                
        elif mergeSpec.status == OPTIONAL:
            if withSpec.status & DEFINED:
                status = DEFINED
                types = set(mergeSpec.types)
            else:
                status = withSpec.status
                types = intersect(mergeSpec.types, withSpec.types)
                if not types:
                    raise AttrError('Incompatible required types of %s, with required types of %s' % (mergeSpec, withSpec))
            
        elif mergeSpec.status & DEFINED:
            status = DEFINED
            if mergeSpec.status & USED: status |= USED
            if withSpec.status & DEFINED: 
                types = set(mergeSpec.types)
                types.update(withSpec.types)
                # In case both definitions are optional we need to relate that to the merged attribute
                if withSpec.status & USED: status |= USED
                if mergeSpec.status & OPTIONAL and withSpec.status & OPTIONAL: status |= OPTIONAL
            else:
                types = set(withSpec.types)
            
        keyargs['status'] = status
        
        defined = set(mergeSpec.defined)
        defined.update(withSpec.defined)
        defined, types = reduce(defined), reduce(types)
        if defined != types and not types.issuperset(defined):
            raise ResolverError('Invalid types %s and defined types %s, they cannot be joined, for %s, and %s, '
                                'from merged:%s\n, with:%s' % (', '.join('\'%s\'' % typ.__name__ for typ in types),
                                 ', '.join('\'%s\'' % typ.__name__ for typ in defined), mergeSpec, withSpec,
                                 ''.join(locationStack(clazz) for clazz in mergeSpec.usedIn),
                                 ''.join(locationStack(clazz) for clazz in withSpec.usedIn)))
        
        keyargs['types'] = types
        keyargs['defined'] = defined
        
        docs = []
        if mergeSpec.doc is not None: docs.append(mergeSpec.doc)
        if withSpec.doc is not None: docs.append(withSpec.doc)
        keyargs['doc'] = '\n'.join(docs) if docs else None
        
        spec = mergeSpec.__class__(**keyargs)
        assert isinstance(spec, Specification), 'Invalid specification %s' % spec
        spec.usedIn.update(mergeSpec.usedIn)
        spec.usedIn.update(withSpec.usedIn)
        
        return spec
    
    def mergeSpecifications(self, mergeSpecs, withSpecs):
        '''
        Merges the provided specifications.
        
        @param mergeSpecs: dictionary{string: Specification}
            The specifications to be merged.
        @param withSpecs: dictionary{string: Specification}
            The specifications to merge with.
        @return: dictionary{string: Specification}
            The merged specifications.
        '''
        assert isinstance(mergeSpecs, dict), 'Invalid specifications %s' % mergeSpecs
        assert isinstance(withSpecs, dict), 'Invalid specifications %s' % withSpecs
        
        specifications = dict(mergeSpecs)
        for name, spec in withSpecs.items():
            ownSpec = specifications.get(name)
            if ownSpec is None: specifications[name] = spec
            else:
                assert isinstance(spec, Specification), 'Invalid specification %s' % spec
                try: specifications[name] = self.mergeSpecification(ownSpec, spec, definedIn=spec.definedIn)
                except AttrError:
                    raise AttrError('Cannot merge attribute \'%s\', from:%s\n, with:%s' % 
                                    (name, ''.join(locationStack(clazz) for clazz in ownSpec.usedIn),
                                     ''.join(locationStack(clazz) for clazz in spec.usedIn)))
        
        return specifications
    
    def solveSpecifications(self, mergeSpecs, withSpecs):
        '''
        Solve the provided specifications.
        
        @param mergeSpecs: dictionary{string: Specification}
            The specifications to be solved.
        @param withSpecs: dictionary{string: Specification}
            The specifications to solve with.
        @return: dictionary{string: Specification}
            The solved specifications.
        '''
        assert isinstance(mergeSpecs, dict), 'Invalid specifications %s' % mergeSpecs
        assert isinstance(withSpecs, dict), 'Invalid specifications %s' % withSpecs
        
        specifications = dict(self.specifications)
        for name, spec in withSpecs.items():
            assert isinstance(spec, Specification), 'Invalid specification %s' % spec
            ownSpec = specifications.get(name)
            if ownSpec is None: specifications[name] = spec
            elif ownSpec.status & DEFINED:
                assert isinstance(ownSpec, Specification), 'Invalid specification %s' % ownSpec
                specifications[name] = self.mergeSpecification(ownSpec, spec, definedIn=spec.definedIn)
            else:
                if spec.definedIn is not None and ownSpec.definedIn is not None:
                    specifications[name] = self.mergeSpecification(spec, ownSpec, definedIn=ownSpec.definedIn)
                else:
                    specifications[name] = self.mergeSpecification(spec, ownSpec)
        
        return specifications
    
    def createDefinitions(self, specifications):
        '''
        Create the definitions attributes.
        
        @param specifications: dictionary{string: Specification}
            The specifications to create the definitions for.
        @return: dictionary{string: IAttribute}
            The created attributes.
        '''
        assert isinstance(specifications, dict), 'Invalid specifications %s' % specifications
        attributes = {}
        for name, spec in specifications.items():
            assert isinstance(name, str), 'Invalid name %s' % name
            assert isinstance(spec, Specification), 'Invalid specification %s' % spec
            attributes[name] = Attribute(spec)
            
        return attributes
        
    def createDescriptors(self, specifications):
        '''
        Create the descriptors attribute.
        
        @param specifications: dictionary{string: Specification}
            The specifications to create the descriptors for.
        @return: dictionary{string: IAttribute}
            The created attributes.
        '''
        assert isinstance(specifications, dict), 'Invalid specifications %s' % specifications
        attributes = {}
        for name, spec in specifications.items():
            assert isinstance(name, str), 'Invalid name %s' % name
            assert isinstance(spec, Specification), 'Invalid specification %s' % spec
            if spec.status == REQUIRED:
                raise AttrError('Cannot generate attribute %s=%s, used in:%s' % 
                                (name, spec, ''.join(locationStack(clazz) for clazz in spec.usedIn)))
            if spec.status & OPTIONAL: continue  # If is optional then no need to create it
            attributes[name] = AttributeObject(spec)
        
        return attributes
    
    def __str__(self):
        if not self.specifications: return '%s empty' % self.__class__.__name__
        return '%s[%s]' % (self.__class__.__name__, ', '.join('%s=%s' % (name, self.specifications.get(name))
                                                              for name in sorted(self.specifications)))

class Attribute(IAttribute):
    '''
    Base attribute implementation for a @see: IAttribute that manages a attributes by status.
    '''
    __slots__ = ('specification', 'Resolver', 'clazz', 'name')

    def __init__(self, specification, Resolver=Resolver):
        '''
        Construct the attribute.
        
        @param specification: Specification
            The attribute specification.
        @param Resolver: class
            The resolver class for the attribute.
        '''
        assert isinstance(specification, Specification), 'Invalid specification %s' % specification
        assert isclass(Resolver), 'Invalid resolver class %s' % Resolver
        
        self.specification = specification
        self.Resolver = Resolver
        
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
            self.clazz, self.name = clazz, name
            self.specification.usedIn[clazz] = self.specification.status
            if self.specification.definedIn is None and self.specification.status == DEFINED:
                self.specification.definedIn = clazz
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
    
    # ----------------------------------------------------------------
    
    def __get__(self, obj, owner=None):
        '''
        Descriptor get.
        '''
        if obj is not None: raise TypeError('Operation not allowed')
        assert self.clazz, 'Attribute %s, is not placed in a class' % self
        return self

    def __set__(self, obj, value):
        '''
        Descriptor set.
        '''
        raise TypeError('Operation not allowed')
    
    def __str__(self):
        st = ''.join((self.__class__.__name__, '.', str(self.specification)))
        if self.clazz:
            return ''.join((st, ' in:', locationStack(self.clazz), ' as attribute ', self.name))
        return ''.join((st, ' unplaced'))

class AttributeObject(Attribute):
    '''
    Object descriptor implementation for a @see: Attribute.
    '''
    __slots__ = ('descriptor',)
    
    def __init__(self, specification, Resolver=Resolver):
        '''
        @see: Attribute.__init__
        '''
        super().__init__(specification, Resolver)
        self.descriptor = None

    def place(self, clazz, name):
        '''
        @see: IAttribute.place
        '''
        if self.clazz is None:
            assert isinstance(clazz, ContextMetaClass), 'Invalid class %s' % clazz
            assert isinstance(name, str), 'Invalid name %s' % name
            
            if __debug__:
                assert hasattr(clazz, name), 'Invalid class %s has no descriptor for %s' % (clazz, name)
                self.descriptor = getattr(clazz, name)
                assert isinstance(self.descriptor, IGet), 'Invalid descriptor %s' % self.descriptor
                assert isinstance(self.descriptor, ISet), 'Invalid descriptor %s' % self.descriptor
                setattr(clazz, name, self)
            self.clazz, self.name = clazz, name
        elif not issubclass(clazz, self.clazz) or self.name != name:
            raise AttrError('%s\n, is already placed in:%s as attribute %s' % (self, locationStack(self.clazz), self.name))
        
    # ----------------------------------------------------------------
    
    def __get__(self, obj, owner=None):
        '''
        @see: Attribute.__get__
        '''
        if obj is None: return self
        assert self.descriptor, 'Attribute %s, is not placed in a class' % self
        try: return self.descriptor.__get__(obj, owner)
        except AttributeError: return None

    def __set__(self, obj, value):
        '''
        @see: Attribute.__set__
        '''
        assert value is None or isinstance(value, self.specification.types), \
        'Invalid value \'%s\' for %s' % (value, self.specification.types)
        assert self.descriptor, 'Attribute %s, is not placed in a class' % self
        self.descriptor.__set__(obj, value)

# --------------------------------------------------------------------

def reduce(types):
    '''
    Reduces the provided types to only the classes that are the top classes.
    
    @param types: Iterable(class)
        The types to reduce.
    @return: set(class)
        The reduced types.
    '''
    assert isinstance(types, Iterable), 'Invalid types %s' % types
    reduced = []
    for clazz in types:
        assert isclass(clazz), 'Invalid class %s' % clazz
        k, solved = 0, False
        while k < len(reduced):
            rclazz = reduced[k]
            
            if rclazz == clazz:
                solved = True
                break
            elif issubclass(clazz, rclazz):
                solved = True
                reduced[k] = clazz
            elif issubclass(rclazz, clazz):
                solved = True
                break
            
            k += 1
            
        if not solved: reduced.append(clazz)
    return set(reduced)

def intersect(first, second):
    '''
    Reduces the provided types to only the classes that are the top classes.
    
    @param first: Iterable(class)
        The first types to reduce.
    @param second: Iterable(class)
        The second types to reduce.
    @return: set(class)
        The intersected types.
    '''
    assert isinstance(first, Iterable), 'Invalid first types %s' % first
    assert isinstance(second, Iterable), 'Invalid types %s' % second
    if not isinstance(second, (list, tuple, set)): second = list(second)
    intersect = []
    for fclazz in first:
        for sclazz in second:
            if issubclass(fclazz, sclazz): intersect.append(sclazz)
            elif issubclass(sclazz, fclazz): intersect.append(fclazz)
    return reduce(intersect)
