'''
Created on Mar 13, 2012

@package: ally api
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the operator types.
'''

from ..type import Type, Input, typeFor, TypeClass
from ally.support.util import immut
from ally.support.util_sys import locationStack
from inspect import ismethod

# --------------------------------------------------------------------
    
def notContainable(other):
    '''
    Provides the is containable flag from the other dictionary.
    
    @param other: dictionary{string: object}
        The other arguments.
    @param value: boolean
        The value to set for the isContainable other argument.
    '''
    assert isinstance(other, dict), 'Invalid other dictionary %s' % other
    assert 'isContainable' not in other, 'Illegal other argument \'isContainable\''
    other['isContainable'] = False
    
def defaultTypeProperty(other, clazz):
    '''
    Sets the default type property if one is not provided, also checks that the default is compatible with the provided one.
    
    @param other: dictionary{string: object}
        The other arguments.
    @param clazz: class
        The type property to default to.
    '''
    assert isinstance(other, dict), 'Invalid other dictionary %s' % other
    assert issubclass(clazz, TypeProperty), 'Invalid type property class %s' % clazz
    if 'TypeProperty' not in other: other['TypeProperty'] = clazz
    else: assert issubclass(other['TypeProperty'], clazz), 'Invalid type property class %s' % other['TypeProperty']

# --------------------------------------------------------------------

class TypeProperty(Type):
    '''
    This type is used to wrap a container property as types.
    '''
    __slots__ = ('parent', 'name', 'type')

    def __init__(self, parent, name, type, **other):
        '''
        Constructs the property type for the provided property name and parent container type.
        @see: Type.__init__
        
        @param parent: TypeContainer
            The container of the property type.
        @param name: string
            The property name that this type represents.
        @param type: Type|None
            The type to associate with the property type, if not provided then the container property type is used.
        @keyword isContainable: boolean
            If true than this type is containable in types like List and Iter.
        '''
        assert isinstance(parent, TypeContainer), 'Invalid container type %s' % parent
        assert isinstance(name, str), 'Invalid property name %s' % name
        assert isinstance(type, Type), 'Invalid type %s' % type

        self.parent = parent
        self.name = name
        self.type = type
        super().__init__(False, other.pop('isContainable', True))
        assert not other, 'Invalid other arguments: %s' % ','.join(other)

    def isOf(self, type):
        '''
        @see: Type.isOf
        '''
        return self == type or self.type.isOf(type)

    def isValid(self, obj):
        '''
        @see: Type.isValid
        '''
        return self.type.isValid(obj)

    def __hash__(self):
        '''
        @see: Type.__hash__
        '''
        return hash((self.parent, self.name))

    def __eq__(self, other):
        '''
        @see: Type.__eq__
        '''
        if isinstance(other, self.__class__):
            return self.parent == other.parent and self.name == other.name
        return False

    def __str__(self):
        '''
        @see: Type.__str__
        '''
        return '%s.%s' % (self.parent, self.name)
    
class TypeContainer(TypeClass):
    '''
    Provides the type for the properties container.
    '''
    __slots__ = ('container', 'properties', 'parents')

    def __init__(self, clazz, namesTypes, **other):
        '''
        Constructs the container type for the provided container.
        @see: TypeClass.__init__
        
        @param clazz: class
            The class associated with the container.
        @param namesTypes: dictionary{string, Type}
            A dictionary containing as a key the property name and as a value the type for property.
        @keyword TypeProperty: class
            The type property class to use for constructing the properties.
        @param properties: immut{string, TypeProperty}
            A dictionary containing as a key the property name and as a value the property type.
        @ivar parents: tuple(TypeContainer)
            The inherited type containers in the inherited order.
        '''
        assert isinstance(namesTypes, dict), 'The names and types properties %s' % namesTypes

        TypeProperty = other.pop('TypeProperty', TypeProperty)
        properties = {}
        for name, type in namesTypes.items():
            assert isinstance(name, str), 'Invalid type name %s' % name
            assert isinstance(type, Type), 'Invalid property type %s' % type
            properties[name] = TypeProperty(self, name, type, **other)
        parents = []
        for parent in self.clazz.__bases__:
            parentType = typeFor(parent)
            if isinstance(parentType, self.__class__): self.parents.append(parentType)
        
        self.properties = immut(properties)
        self.parents = tuple(parents)
        super().__init__(clazz, False, True)

# --------------------------------------------------------------------

class TypeModelProperty(TypeProperty):
    '''
    This type is used to wrap a model property as types.
    '''
    __slots__ = ('isId', 'model')

    def __init__(self, parent, name, type, **other):
        '''
        Constructs the property type for the provided property name and parent container type.
        @see: TypeProperty.__init__
        
        @param parent: TypeModel
            The model of the property type.
        @ivar isId: boolean
            True if the property type represents a property id, False otherwise.
        @ivar model: TypeModel|None
            The type model that the property represents if one is available.
        '''
        assert isinstance(parent, TypeModel), 'Invalid model type %s' % parent
        
        self.isId = other.pop('id', None) == name
        if isinstance(type, TypeModel):
            assert isinstance(type.propertyId, TypeModelProperty), 'A property id is required for:%s\n,in order '\
            'to be used as a referenced model for \'%s\'' % (locationStack(type.clazz), name)
            self.model = type
            type = type.propertyId.type
        else: self.model = None
        assert isinstance(type, Type), 'Invalid type %s' % type
        assert type.isPrimitive, 'Invalid type %s for property \'%s\', only primitives or models allowed' % (type, name)
        
        super().__init__(parent, name, type, **other)
    
class TypeModel(TypeContainer):
    '''
    Provides the type for the model.
    '''
    __slots__ = ('name', 'hints', 'propertyId')

    def __init__(self, clazz, namesTypes, name, **other):
        '''
        Constructs the model type for the provided properties.
        @see: TypeContainer.__init__
        
        @param name: string
            The name of the model.
        @keyword id: string|None
            The property that represent the id of the model, if None then it means the model doesn't poses an id.
        @keyword hints: dictionary{string, object}|None
            The hints associated with the model.
        @ivar hints: immut{string, object}
            The immutable hints.
        @ivar propertyId: TypeModelProperty|None
            The type model property id of the model if one is available.
        '''
        assert isinstance(name, str) and name, 'Invalid model name %s' % name
        
        self.name = name
        hints = other.pop('hints', None)
        if hints is not None:
            assert isinstance(hints, dict), 'Invalid hints %s' % hints
            if __debug__:
                for hintn in hints: assert isinstance(hintn, str), 'Invalid hint name %s' % hintn
            self.hints = immut(hints)
        else: self.hints = immut()
        
        defaultTypeProperty(other, TypeModelProperty)
        super().__init__(clazz, namesTypes, **other)
        
        nameId = other['id']
        if nameId is not None:
            assert nameId in self.properties, 'Invalid id property %s' % nameId
            self.propertyId = self.properties[nameId]
        else: self.propertyId = None

# --------------------------------------------------------------------

class TypeCriteria(TypeContainer):
    '''
    Provides the type for the criteria.
    '''
    __slots__ = ('main',)

    def __init__(self, clazz, namesTypes, **other):
        '''
        Constructs the criteria type for the provided properties.
        @see: TypeContainer.__init__
        
        @keyword main: list[string]|tuple(string)
            The main properties for the criteria, the main is used whenever a value is set directly on the 
            criteria. The main properties needs to be found in the provided properties and have compatible types.
        @ivar main: tuple(string)
            The immutable main.
        '''
        assert isinstance(namesTypes, dict), 'The names and types properties %s' % namesTypes
        if __debug__:
            for name, type in namesTypes.values():
                assert isinstance(type, Type), 'Invalid type %s for \'%s\'' % (type, name)
                assert type.isPrimitive, 'Not a primitive type %s for \'%s\'' % (type, name)

        main = other.pop('main', None)
        if main:
            assert isinstance(main, (list, tuple)), 'Invalid main properties %s' % main
            if __debug__:
                type = None
                for name in main:
                    assert name in namesTypes, 'Invalid main property \'%s\', is not found in properties' % name
                    if type is not None:
                        assert namesTypes[name].isOf(type), \
                        'Invalid main property \'%s\' with type %s expected %s' % (name, namesTypes[name], type)
                    else: type = namesTypes[name]
            self.main = tuple(main)
        else: self.main = ()
        
        notContainable(other)
        super().__init__(clazz, namesTypes, **other)

class TypeCriteriaEntry(TypeProperty):
    '''
    This type is used to wrap a query criteria.
    '''
    __slots__ = ()

    def __init__(self, parent, name, type, **other):
        '''
        Constructs the criteria type for the provided criteria name and parent query type.
        @see: TypeProperty.__init__
        
        @param parent: TypeQuery
            The query type of the criteria type.
        @param name: string
            The criteria name represented by the type.
        '''
        assert isinstance(parent, TypeQuery), 'Invalid query type %s' % parent
        assert isinstance(type, TypeCriteria), 'Invalid criteria type %s' % type
        
        notContainable(other)
        super().__init__(parent, name, type, **other)

class TypeQuery(TypeContainer):
    '''
    Provides the type for the query.
    '''
    __slots__ = ('model',)

    def __init__(self, clazz, namesTypes, model, **other):
        '''
        Constructs the query type for the provided query.
        @see: TypeContainer.__init__
        
        @param model: TypeModel
            The type model that is this type query is owned by.
        '''
        assert isinstance(namesTypes, dict), 'The names and types properties %s' % namesTypes
        assert isinstance(model, TypeModel), 'Invalid owner %s' % model

        self.model = model
        
        defaultTypeProperty(other, TypeCriteriaEntry)
        super().__init__(clazz, namesTypes, **other)

# --------------------------------------------------------------------

class TypeExtension(TypeContainer):
    '''
    Provides the type for the extensions.
    @attention: The criteria will allow only for primitive types.
    '''
    __slots__ = ()

    def __init__(self, clazz, namesTypes, **other):
        '''
        Constructs the extension type for the provided properties.
        @see: TypeContainer.__init__
        '''
        assert isinstance(namesTypes, dict), 'The names and types properties %s' % namesTypes
        if __debug__:
            for name, type in namesTypes.values():
                assert isinstance(type, Type), 'Invalid type %s for \'%s\'' % (type, name)
                assert type.isPrimitive, 'Not a primitive type %s for \'%s\'' % (type, name)
        
        notContainable(other)
        super().__init__(clazz, namesTypes, **other)
        
# --------------------------------------------------------------------

class TypeOptionProperty(TypeProperty):
    '''
    This type is used to wrap a option property as types.
    '''

    def __init__(self, parent, property, type, **other):
        '''
        Constructs the property type for the provided property name and parent container type.
        @see: TypeProperty.__init__
        
        @param parent: TypeOption
            The model of the property type.
        '''
        assert isinstance(parent, TypeOption), 'Invalid option type %s' % parent
        
        notContainable(other)
        super().__init__(parent, property, type, **other)

class TypeOption(TypeContainer):
    '''
    Provides the type for the option.
    '''
    __slots__ = ()

    def __init__(self, clazz, namesTypes, **other):
        '''
        Constructs the option type for the provided properties.
        @see: TypeContainer.__init__
        '''
        notContainable(other)
        defaultTypeProperty(other, TypeOptionProperty)
        super().__init__(clazz, namesTypes, **other)
        
# --------------------------------------------------------------------

class Call:
    '''
    Provides the container for a service call. This class will basically contain all the types that are involved in
    input and output from the call.
    '''
    __slots__ = ('name', 'method', 'output', 'inputs', 'hints')

    def __init__(self, name, method, inputs, output, hints=None):
        '''
        Constructs an API call that will have the provided input and output types.
        
        @param name: string
            The name of the function represented by the call.
        @param method: integer
            The method of the call, can be one of GET, INSERT, UPDATE or DELETE constants in this module.
        @param inputs: list[Input]|tuple(Input)
            A list containing all the Input's of the call.
        @param output: Type
            The output type for the service call.
        @param hints: dictionary{string: object}|None
            The hints associated with the call.
        '''
        assert isinstance(name, str) and name.strip(), 'Provide a valid name'
        assert isinstance(method, int), 'Invalid method %s' % method
        assert isinstance(inputs, (list, tuple)), 'Invalid inputs %s, needs to be a list' % inputs
        assert isinstance(output, Type), 'Invalid output type %s' % output
        
        if __debug__:
            for inp in inputs: assert isinstance(inp, Input), 'Not an input %s' % input
        if hints is not None:
            assert isinstance(hints, dict), 'Invalid hints %s' % hints
            if __debug__:
                for hintn in hints: assert isinstance(hintn, str), 'Invalid hint name %s' % hintn
            hints = immut(hints)
        else: hints = immut()

        self.name = name
        self.method = method
        self.inputs = tuple(inputs)
        self.output = output
        self.hints = hints

    def __str__(self):
        inputs = [''.join(('defaulted:' if inp.hasDefault else '', inp.name, '=', str(inp.type))) for inp in self.inputs]
        return '%s(%s)->%s' % (self.name, ', '.join(inputs), self.output)
    
class TypeCall(Type):
    '''
    Provides the type for the service call.
    '''
    __slots__ = ('parent', 'call')

    def __init__(self, parent, call):
        '''
        Constructs the service call type.
        @see: Type.__init__
        
        @param parent: TypeService
            The parent service type.
        @param call: Call
            The call for call type.
        '''
        assert isinstance(parent, TypeService), 'Invalid parent %s' % parent
        assert isinstance(call, Call), 'Invalid call %s' % call
        super().__init__(False, False)

        self.parent = parent
        self.call = call

    def isOf(self, type):
        '''
        @see: Type.isOf
        '''
        return self == typeFor(type)

    def isValid(self, obj):
        '''
        @see: Type.isValid
        '''
        if not ismethod(obj): return False
        return isinstance(obj.__self__, self.parent.clazz)

    def __hash__(self):
        '''
        @see: Type.__hash__
        '''
        return hash((self.parent, self.call.name))

    def __eq__(self, other):
        '''
        @see: Type.__eq__
        '''
        if isinstance(other, self.__class__): return self.parent == other.parent and self.call.name == other.call.name
        return False

    def __str__(self):
        '''
        @see: Type.__str__
        '''
        return '%s.%s' % (self.parent, self.call)
    
class TypeService(TypeClass):
    '''
    Provides the type for the service.
    '''
    __slots__ = ('service',)

    def __init__(self, clazz, calls):
        '''
        Constructs the service type for the provided service.
        @see: TypeClass.__init__
        
        @param calls: list[Call]|tuple(Call)
            The calls list that belong to this service class.
        @ivar calls: dictionary{string: TypeCall}
            The type calls of the service.
        '''
        assert isinstance(calls, (list, tuple)), 'Invalid calls %s, needs to be a list' % calls
        super().__init__(clazz, False, False)
        
        self.calls = immut({call.name: TypeCall(self, call.name) for call in calls})

