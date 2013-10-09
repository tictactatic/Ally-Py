'''
Created on Jul 12, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides verifiers for definitions.
'''

from ally.api.operator.type import TypeProperty, TypeModel
from ally.api.type import typeFor, Input, Type
from ally.core.spec.definition import IVerifier, IValue
from ally.design.processor.attribute import requires, optional
from ally.design.processor.context import Context
from ally.design.processor.resolvers import merge
from ally.support.api.util_service import isCompatible
from ally.support.util import Singletone
from ally.support.util_context import findFirst
from inspect import isclass

# --------------------------------------------------------------------

class VerifierOperator(IVerifier):
    '''
    Base class for @see: IVerifier that allows for operators between them.
    '''

    def __and__(self, other):
        '''
        Apply the 'and' operator.
        '''
        assert isinstance(other, IVerifier), 'Invalid verifier %s' % other
        return VerifierAnd(self, other)

    def __or__(self, other):
        '''
        Apply the 'or' operator.
        '''
        assert isinstance(other, IVerifier), 'Invalid verifier %s' % other
        return VerifierOr(self, other)

class VerifierOr(VerifierOperator):
    '''
    Implementation for a @see: IVerifier that aplies an 'or' operator between verifiers.
    '''

    def __init__(self, *verifiers):
        '''
        Construct the 'or' verifier.

        @param verifiers: arguments[IVerifier]
            The verifiers to apply the 'or' for.
        '''
        assert verifiers, 'At least one verifier is required'
        if __debug__:
            for verifier in verifiers: assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
        self.verifiers = verifiers

    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        for verifier in self.verifiers:
            assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
            verifier.prepare(resolvers)

    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        for verifier in self.verifiers:
            assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
            if verifier.isValid(definition): return True
        return False

class VerifierAnd(VerifierOperator):
    '''
    Implementation for a @see: IVerifier that aplies an 'and' operator between verifiers.
    '''

    def __init__(self, *verifiers):
        '''
        Construct the 'and' verifier.

        @param verifiers: arguments[IVerifier]
            The verifiers to apply the 'and' for.
        '''
        assert verifiers, 'At least one verifier is required'
        if __debug__:
            for verifier in verifiers: assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
        self.verifiers = verifiers

    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        for verifier in self.verifiers:
            assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
            verifier.prepare(resolvers)

    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        for verifier in self.verifiers:
            assert isinstance(verifier, IVerifier), 'Invalid verifier %s' % verifier
            if not verifier.isValid(definition): return False
        return True

class Category(VerifierOperator):
    '''
    Implementation for a @see: IVerifier that validates for a definition category.
    '''

    class Definition(Context):
        '''
        The definition context.
        '''
        # ---------------------------------------------------------------- Required
        category = requires(str)

    def __init__(self, *categories):
        '''
        Construct the category verifier.

        @param categories: arguments[string]
            The categories to verify for.
        '''
        assert categories, 'At least one category is required'
        if __debug__:
            for category in categories: assert isinstance(category, str), 'Invalid category %s' % category
        self.categories = set(categories)

    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=Category.Definition))

    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, Category.Definition), 'Invalid definition %s' % definition
        return definition.category in self.categories

class Name(VerifierOperator):
    '''
    Implementation for a @see: IVerifier that validates for a definition name.
    '''

    class Definition(Context):
        '''
        The definition context.
        '''
        # ---------------------------------------------------------------- Required
        name = requires(str)

    def __init__(self, *names):
        '''
        Construct the name verifier.

        @param name: arguments[string]
            The names to verify for.
        '''
        assert names, 'At least one name is required'
        if __debug__:
            for name in names: assert isinstance(name, str), 'Invalid name %s' % name
        self.names = set(names)

    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=Name.Definition))

    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, Name.Definition), 'Invalid definition %s' % definition
        return definition.name in self.names

class InputType(VerifierOperator):
    '''
    Implementation for a @see: IVerifier that validates for a specific input type,
    the first definition input will be checked.
    '''

    class Definition(Context):
        '''
        The definition context.
        '''
        # ---------------------------------------------------------------- Required
        decoding = requires(Context)

    class Decoding(Context):
        '''
        The decoding context.
        '''
        # ---------------------------------------------------------------- Optional
        parent = optional(Context)
        input = optional(Input)

    def __init__(self, *types, check=lambda own, found: own == found):
        '''
        Construct the input type verifier.

        @param types: arguments[Type container]
            The type(s) to check for.
        @param check: callable(own, found) -> boolean
            The check function to use, it will receive as parameters the verified type and the found type.
        '''
        assert types, 'At least one type is required'
        assert callable(check), 'Invalid check callable %s' % check

        self.types = set()
        for type in types:
            typ = typeFor(type)
            assert isinstance(typ, Type), 'Invalid type %s' % type
            self.types.add(typ)

        self.check = check

    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=InputType.Definition, Decoding=InputType.Decoding))

    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, InputType.Definition), 'Invalid definition %s' % definition
        if not definition.decoding: return False
        input = findFirst(definition.decoding, InputType.Decoding.parent, InputType.Decoding.input)
        if input:
            assert isinstance(input, Input), 'Invalid input %s' % input
            for typ in self.types:
                if self.check(typ, input.type): return True
        return False

class Property(VerifierOperator):
    '''
    Implementation for a @see: IVerifier that validates for a specific property,
    the first definition property will be checked.
    '''

    class Decoding(Context):
        '''
        The decoding context.
        '''
        # ---------------------------------------------------------------- Optional
        parent = optional(Context)
        property = optional(TypeProperty)

    def __init__(self, *properties):
        '''
        Construct the property verifier.

        @param properties: arguments[TypeProperty container]
            The properties types to verify for.
        '''
        assert properties, 'At least one property is required'

        self.properties = set()
        for prop in properties:
            typ = typeFor(prop)
            assert isinstance(typ, TypeProperty), 'Invalid property type %s' % prop
            self.properties.add(typ)

    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=InputType.Definition, Decoding=Property.Decoding))

    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, InputType.Definition), 'Invalid definition %s' % definition
        if not definition.decoding: return False
        property = findFirst(definition.decoding, Property.Decoding.parent, Property.Decoding.property)
        if property:
            if property in self.properties: return True
            for prop in self.properties:
                if isCompatible(prop, property): return True
        return False

class PropertyType(VerifierOperator):
    '''
    Implementation for a @see: IVerifier that validates that a property represents the provided types.
    '''

    def __init__(self, *classes):
        '''
        Construct the property type verifier.

        @param classes: arguments[class]
            The properties types to verify for.
        '''
        assert classes, 'At least one classes is required'
        if __debug__:
            for clazz in classes: assert isclass(clazz), 'Invalid class %s' % clazz
        self.classes = classes

    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=InputType.Definition, Decoding=Property.Decoding))

    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, InputType.Definition), 'Invalid definition %s' % definition
        if not definition.decoding: return False
        prop = findFirst(definition.decoding, Property.Decoding.parent, Property.Decoding.property)
        if prop:
            assert isinstance(prop, TypeProperty), 'Invalid property type %s' % prop
            for clazz in self.classes:
                if prop.isOf(clazz): return True
        return False

class PropertyTypeOf(VerifierOperator):
    '''
    Implementation for a @see: IVerifier that validates for a specific property type,
    the first definition property will be checked.
    '''

    def __init__(self, *types):
        '''
        Construct the property type verifier.

        @param types: arguments[class]
            The properties types to verify for.
        '''
        assert types, 'At least one property type is required'
        if __debug__:
            for typ in types: assert isclass(typ), 'Invalid class %s' % typ
        self.types = types

    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=InputType.Definition, Decoding=Property.Decoding))

    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, InputType.Definition), 'Invalid definition %s' % definition
        if not definition.decoding: return False
        prop = findFirst(definition.decoding, Property.Decoding.parent, Property.Decoding.property)
        if prop:
            assert isinstance(prop, TypeProperty), 'Invalid property type %s' % prop
            return isinstance(prop.type, self.types)
        return False

class ModelId(VerifierOperator, Singletone):
    '''
    Implementation for a @see: IVerifier that validates for model id properties types,
    the first definition property will be checked.
    '''

    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=InputType.Definition, Decoding=Property.Decoding))

    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, InputType.Definition), 'Invalid definition %s' % definition
        if not definition.decoding: return False
        prop = findFirst(definition.decoding, Property.Decoding.parent, Property.Decoding.property)
        if prop:
            assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
            if isinstance(prop.parent, TypeModel):
                assert isinstance(prop.parent, TypeModel)
                return prop.parent.propertyId == prop
        return False

# --------------------------------------------------------------------

class ReferencesNames(IValue, Singletone):
    '''
    Implementation for a @see: IValue that provides the references names.
    '''

    class Definition(Context):
        '''
        The definition context.
        '''
        # ---------------------------------------------------------------- Optional
        references = optional(list)
        # ---------------------------------------------------------------- Required
        name = requires(str)

    def prepare(self, resolvers):
        '''
        @see: IValue.prepare
        '''
        merge(resolvers, dict(Definition=ReferencesNames.Definition))

    def get(self, definition):
        '''
        @see: IValue.get
        '''
        assert isinstance(definition, ReferencesNames.Definition), 'Invalid definition %s' % definition
        names = []
        if ReferencesNames.Definition.references in definition and definition.references:
            for defin in definition.references:
                assert isinstance(defin, ReferencesNames.Definition), 'Invalid definition %s' % defin
                if defin.name: names.append(defin.name)
        return names
