'''
Created on Mar 13, 2012

@package: ally api
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the operator descriptors for the APIs.
'''

from ..type import typeFor, Type, TypeSupport
from .type import TypeContainer, TypeProperty, TypeQuery, TypeCriteria, TypeCall, \
    TypeService
from abc import ABCMeta
from ally.api.operator.type import TypePropertyContainer
from ally.support.util_spec import IGet, IContained, ISet, IDelete
from ally.support.util_sys import getAttrAndClass
from inspect import isclass
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Reference(TypeSupport):
    '''
    Provides the property reference that is provided by the property descriptor.
    '''

    def __init__(self, type, parent=None):
        '''
        Constructs the container property descriptor.
        
        @param type: TypeProperty
            The property type represented by the property.
        '''
        assert isinstance(type, TypeProperty), 'Invalid property type %s' % type
        assert parent is None or isinstance(parent, TypeSupport), \
        'Invalid parent %s, needs to be a type support' % parent
        super().__init__(type)

        self._ally_ref_parent = parent
        self._ally_ref_children = {}

    def __getattr__(self, name):
        '''
        Provides the contained container properties.
        
        @param name: string
            The property to get from the contained container.
        @return: object
            The reference for the container property.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        reference = self._ally_ref_children.get(name)
        if reference is None:
            if isinstance(self._ally_type, TypePropertyContainer): container = self._ally_type.container
            else: container = self._ally_type.type
            if isinstance(container, TypeContainer):
                assert isinstance(container, TypeContainer)
                prop = container.properties.get(name)
                if prop: reference = self._ally_ref_children[name] = Reference(prop, self)
            if reference is None:
                raise AttributeError('\'%s\' object has no attribute \'%s\'' % (self.__class__.__name__, name))
        return reference

    def __hash__(self):
        return hash(self._ally_type)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._ally_type == other._ally_type
        return False

    def __str__(self):
        st = []
        if self._ally_ref_parent:
            st.append(str(self._ally_ref_parent))
            st.append('->')
        st.append(str(self._ally_type))
        return ''.join(st)

class Property(IGet, IContained, ISet, IDelete):
    '''
    Provides the descriptor for properties. It contains the operation that need to be applied on a model
    object that relate to this property. The property also has a reference that will be returned whenever the property
    is used only with the model class.
    '''

    def __init__(self, name):
        '''
        Constructs the model property descriptor.
        
        @param name: string
            The property name.
        '''
        assert isinstance(name, str), 'Invalid property name %s' % name

        self.name = name

    def __get__(self, obj, clazz=None):
        '''
        @see: IGet.__get__
        '''
        if obj is None: return clazz._ally_reference.get(self.name)
        return obj.__dict__.get(self.name)

    def __contained__(self, obj):
        '''
        @see: IContained.__contained__
        '''
        return self.name in obj.__dict__

    def __set__(self, obj, value):
        '''
        @see: ISet.__set__
        '''
        obj.__dict__[self.name] = value
        assert log.debug('Success on setting value (%s) for %s', value, self) or True

    def __delete__(self, obj):
        '''
        @see: IDelete.__delete__
        '''
        if self.name in obj.__dict__:
            del obj.__dict__[self.name]
            assert log.debug('Success on removing value for %s', self) or True

class CriteriaEntry(Reference):
    '''
    Descriptor used for defining criteria entries in a query object.
    '''

    def __init__(self, type):
        '''
        Construct the criteria entry descriptor.
        
        @param type: TypeProperty
            The criteria entry property type represented by the criteria entry descriptor.
        '''
        assert isinstance(type, TypeProperty), 'Invalid property type %s' % type
        assert isinstance(type.type, TypeCriteria), 'Invalid criteria type %s' % type.type
        super().__init__(type)

    def __get__(self, obj, clazz=None):
        '''
        Provides the value represented by this criteria entry for the provided query object.
        
        @param obj: object
            The query object to provide the value for, None provides the criteria entry.
        @param clazz: class
            The query class from which the criteria originates from, can be None if the object is provided.
        @return: object
            The value of the criteria or the criteria entry if used only with the class.
        '''
        if obj is None: return self
        else:
            objCrit = obj.__dict__.get(self._ally_type.name)
            if objCrit is None:
                objCrit = self._ally_type.type.clazz()
                obj.__dict__[self._ally_type.name] = objCrit
                assert log.debug('Created criteria object for %s', self) or True
            return objCrit

    def __contained__(self, obj):
        '''
        Checks if the entry is contained in the provided object. This is an artifact from the __contains__ method 
        that is found on the actual model object.
        
        @param obj: object
            The object to check if the entry is contained in.
        @return: boolean
            True if the entry is contained in the object, false otherwise.
        '''
        return self._ally_type.name in obj.__dict__

    def __set__(self, obj, value):
        '''
        Set the value on the main criteria property, if the represented criteria does not expose a main property that this
        set method will fail.
        
        @param obj: object
            The query object to set the value to.
        @param value: object
            The value to set, needs to be valid for the main property.
        '''
        if not self._ally_type.type.main:
            raise ValueError('Cannot set value for %s because the %s has no main property' % (self, self._ally_type.parent))
        objCrit = self.__get__(obj)
        for name in self._ally_type.type.main: setattr(objCrit, name, value)

    def __delete__(self, obj):
        '''
        Remove the criteria represented by this criteria entry from the provided query object.
        
        @param obj: object
            The query object to remove the value from.
        '''
        if self._ally_type.name in obj.__dict__:
            del obj.__dict__[self._ally_type.name]
            assert log.debug('Success on removing value for %s', self) or True

class CallAPI(TypeSupport):
    '''
    Provides the call reference that is provided by the service call descriptor.
    '''
    
    def __init__(self, type):
        '''
        Constructs the container call descriptor.
        
        @param type: TypeCall
            The call type represented by the reference.
        '''
        assert isinstance(type, TypeCall), 'Invalid call type %s' % type
        TypeSupport.__init__(self, type)
        
        for name, input in type.inputs.items(): setattr(self, name, input)
        
    def __call__(self, *args, **keyargs):
        raise TypeError('Cannot use an API service call that is not implemented')

    def __hash__(self):
        return hash(self._ally_type)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._ally_type == other._ally_type
        return False

    def __str__(self):
        return str(self._ally_type)
 
# --------------------------------------------------------------------

class Container:
    '''
    Support class for containers.
    '''
    
    def __contains__(self, ref):
        '''
        Checks if the object contains a value for the property even if that value is None.
        
        @param ref: TypeProperty reference
            The type property to check.
        @return: boolean
            True if a value for the reference is present, false otherwise.
        '''
        prop = typeFor(ref)
        if not isinstance(prop, TypeProperty): return False
        assert isinstance(prop, TypeProperty)
        assert isinstance(prop.parent, TypeContainer), 'Invalid parent for %s' % prop
        if prop.parent.isValid(self):
            descriptor, _clazz = getAttrAndClass(self.__class__, prop.name)
            if not isinstance(descriptor, IContained): return True
            # In case the descriptor has no contained method we consider that the property should always be present.
            assert isinstance(descriptor, IContained)
            return descriptor.__contained__(self)
        return False

    def __str__(self):
        '''
        Represent the container instance.
        '''
        container = typeFor(self)
        assert isinstance(container, TypeContainer), 'Invalid container %s' % self.__class__
        return '%s[%s]' % (self.__class__.__name__, ','.join('%s=%s' % (name, getattr(self, name))
                            for name, prop in container.properties.items() if self.__contains__(prop)))

class Query(Container):
    '''
    Support class for queries.
    '''
    
    def __init__(self, **keyargs):
        '''
        Construct the instance of the query by automatically setting as criterias the values provides as key arguments.
        '''
        query = typeFor(self)
        assert isinstance(query, TypeQuery), 'Invalid query %s' % self
        for name, value in keyargs.items():
            if name not in query.properties: raise ValueError('Invalid criteria name \'%s\' for %s' % (name, query))
            setattr(self, name, value)

    def __contains__(self, ref):
        '''
        Checks if the object contains a value for the property even if that value is None.
        
        @param ref: TypeCriteriaEntry|TypeProperty reference
            The type property to check.
        @return: boolean
            True if a value for the reference is present, false otherwise.
        '''
        entry = typeFor(ref)
        if not isinstance(entry, TypeProperty): return False
        assert isinstance(entry, TypeProperty)
        
        if not isinstance(entry.parent, TypeQuery):
            # We do not need to make any recursive checking here since the criteria will only contain primitive properties
            # so there will not be the case of AQuery.ACriteria.AModel.AProperty the maximum is AQuery.ACriteria.AProperty
            prop = entry
            try: entry = typeFor(ref._ally_ref_parent)
            except AttributeError: return False
            if not isinstance(entry.parent, TypeQuery): return False
        else: prop = None
            
        assert isinstance(entry.parent, TypeQuery)
        if not entry.parent.isValid(self): return False
        
        descriptor, _clazz = getAttrAndClass(self.__class__, entry.name)
        if not isinstance(descriptor, IContained): return False
        
        assert isinstance(descriptor, IContained)
        if not descriptor.__contained__(self): return False
        
        if prop:
            if not isinstance(descriptor, IGet): return False
            assert isinstance(descriptor, IGet)
            return prop in descriptor.__get__(self)
        
        return True
    
# --------------------------------------------------------------------

def processWithProperties(clazz, container):
    '''
    Processes the provided class as a container with properties.
    
    @param clazz: class
        The class to be processed.
    @param container: TypeContainer
        The container to process with.
    @return: class
        The processed class.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    assert isinstance(container, TypeContainer), 'Invalid container %s' % container
    
    if not issubclass(clazz, Container):
        attributes = dict(clazz.__dict__)
        attributes.pop('__dict__', None)  # Removing __dict__ since is a reference to the old class dictionary.
        attributes.pop('__weakref__', None)
        bases = [base for base in clazz.__bases__ if base != object]
        bases.append(Container)
        clazz = container.clazz = type(clazz.__name__, tuple(bases), attributes)
    
    clazz._ally_type = container
    clazz._ally_reference = {name: Reference(prop) for name, prop in container.properties.items()}
    
    for name in container.properties:
        if not hasattr(clazz, name): setattr(clazz, name, Property(name))
    
    return clazz
    
def processAsQuery(clazz, query):
    '''
    Processes the provided class as a query.
    
    @param clazz: class
        The class to be processed.
    @param query: TypeQuery
        The query to process with.
    @return: class
        The processed class.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    assert isinstance(query, TypeQuery), 'Invalid query %s' % query
    
    if not isinstance(clazz, Query):
        attributes = dict(clazz.__dict__)
        attributes.pop('__dict__', None)  # Removing __dict__ since is a reference to the old class dictionary.
        attributes.pop('__weakref__', None)
        bases = [base for base in clazz.__bases__ if base != object]
        bases.append(Query)
        clazz = query.clazz = type(clazz.__name__, tuple(bases), attributes)
    
    clazz._ally_type = query
    for name, prop in query.properties.items(): setattr(clazz, name, CriteriaEntry(prop))
    
    return clazz

def processAsService(clazz, service):
    '''
    Processes the provided class as a service.
    
    @param clazz: class
        The class to be processed.
    @param service: TypeService
        The service to process with.
    @return: class
        The processed class.
    '''
    assert isclass(clazz), 'Invalid class %s' % clazz
    assert isinstance(service, TypeService), 'Invalid service %s' % service
    
    if type(clazz) != ABCMeta:
        attributes = dict(clazz.__dict__)
        attributes.pop('__dict__', None)  # Removing __dict__ since is a reference to the old class dictionary.
        attributes.pop('__weakref__', None)
        clazz = service.clazz = ABCMeta(clazz.__name__, clazz.__bases__, attributes)
        
    abstract = set(clazz.__abstractmethods__)
    abstract.update(service.calls)
    
    clazz.__abstractmethods__ = frozenset(abstract)
    clazz._ally_type = service
    for name, callType in service.calls.items():
        callAPI = CallAPI(callType)
        callAPI.__isabstractmethod__ = True  # Flag that notifies the ABCMeta that is is an actual abstract method.
        # We provide the original function code and name.
        callAPI.__code__ = getattr(clazz, name).__code__  
        callAPI.__name__ = getattr(clazz, name).__name__
        setattr(clazz, name, callAPI)

    return clazz

# --------------------------------------------------------------------

def typesFor(ref):
    '''
    Provides the types of the provided references. This function provides a list of types that represent the references.
    
    ex:
        @model
        class Entity:
            Name = Integer
        
        @model
        class EntityContainer1:
            Entity = Entity
            
        @model
        class EntityContainer2:
            EntityContainer = EntityContainer1 
            
        typesOf(EntityContainer2.EntityContainer.Entity.Name) will return:
        [EntityContainer2.EntityContainer, EntityContainer1.Entity, Entity.Name]
    
    @param ref: object
        The reference object to provide the types for.
    @return: list[Type]
        The list of types of the reference.
    '''
    assert ref is not None, 'None is not a valid reference'
    types = []
    while ref:
        typ = typeFor(ref)
        assert isinstance(typ, Type), 'Invalid reference %s, has no type' % ref
        types.insert(0, typ)
        try: ref = ref._ally_ref_parent
        except AttributeError: ref = None
    return types
