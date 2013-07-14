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
from ally.core.spec.transform.encdec import Category
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.resolvers import merge
from ally.support.api.util_service import isCompatible
import abc

# --------------------------------------------------------------------

class IVerifier(metaclass=abc.ABCMeta):
    '''
    Description verifier for definition specification.
    '''
    
    def prepare(self, resolvers):
        '''
        Prepare the resolvers contexts for the trigger.
        
        @param resolvers: dictionary{string, IResolver}
            The resolvers to prepare.
        '''
    
    @abc.abstractmethod
    def isValid(self, definition):
        '''
        Checks if the provided definition is valid for the trigger.
        
        @param definition: Context
            The definition to check.
        @return: boolean
            True if the definition is checked by the trigger, False otherwise.
        '''

# --------------------------------------------------------------------

class VerifyInfo(IVerifier):
    '''
    Implementation for a @see: IVerifier that validates for a series of provided keys.
    '''
    
    class Definition(Context):
        '''
        The definition context.
        '''
        # ---------------------------------------------------------------- Required
        info = requires(dict)
    
    def __init__(self, *info):
        '''
        Construct the info verifier.
        
        @param info: arguments[string]
            The info keys to trigger for, all provided key need to be available in order to validate.
        '''
        assert info, 'At least one info key is required'
        if __debug__:
            for key in info: assert isinstance(key, str), 'Invalid info key %s' % key
        
        self.info = set(info)
        
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=VerifyInfo.Definition))
        
    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, VerifyInfo.Definition), 'Invalid definition %s' % definition
        
        if not definition.info: return False
        return self.info.issubset(definition.info)
    
class VerifyCategory(IVerifier):
    '''
    Implementation for a @see: IVerifier that validates for a definition category.
    '''
    
    class Definition(Context):
        '''
        The definition context.
        '''
        # ---------------------------------------------------------------- Required
        category = requires(Category)
    
    def __init__(self, category):
        '''
        Construct the category verifier.
        
        @param category: Category
            The category to verify for.
        '''
        assert isinstance(category, Category), 'Invalid category %s' % category
        
        self.category = category
        
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=VerifyCategory.Definition))
        
    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, VerifyCategory.Definition), 'Invalid definition %s' % definition
        return self.category.isValid(definition.category)

class VerifyName(VerifyInfo, VerifyCategory):
    '''
    Extension for a @see: VerifyInfo, VerifyCategory that validates also for a specific name.
    '''

    class Definition(Context):
        '''
        The definition context.
        '''
        # ---------------------------------------------------------------- Required
        name = requires(str)
    
    def __init__(self, name, *info, category=None):
        '''
        Construct the name verifier.
        @see: VerifyInfo.__init__
        
        @param name: string
            The name to verify for.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        if info: VerifyInfo.__init__(self, *info)
        else: self.info = None
        if category: VerifyCategory.__init__(self, category)
        else: self.category = None
        
        self.name = name
        
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=VerifyName.Definition))
        if self.info: VerifyInfo.prepare(self, resolvers)
        if self.category: VerifyCategory.prepare(self, resolvers)
        
    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, VerifyName.Definition), 'Invalid definition %s' % definition
        if self.name != definition.name: return False
        
        if self.info and not VerifyInfo.isValid(self, definition): return False
        if self.category and not VerifyCategory.isValid(self, definition): return False
        return True
    
class VerifyType(VerifyInfo):
    '''
    Extension for a @see: VerifyInfo that validates also for a specific input type.
    '''

    class Definition(Context):
        '''
        The definition context.
        '''
        # ---------------------------------------------------------------- Required
        solicitation = requires(Context)
        
    class Solicitation(Context):
        '''
        The solicitation context.
        '''
        # ---------------------------------------------------------------- Required
        input = requires(Input)
    
    def __init__(self, the, *info, check=lambda own, found: own == found):
        '''
        Construct the type verifier.
        @see: VerifyInfo.__init__
        
        @param the: Type container
            The type to check for.
        @param check: callable(own, found) -> boolean
            The check function to use, it will receive as parameters the verified type and the found type.
        '''
        the = typeFor(the)
        assert isinstance(the, Type), 'Invalid property %s' % the
        assert callable(check), 'Invalid check callable %s' % check
        if info: VerifyInfo.__init__(self, *info)
        else: self.info = None
        
        self.type = the
        self.check = check
        
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=VerifyType.Definition, Solicitation=VerifyType.Solicitation))
        if self.info: VerifyInfo.prepare(self, resolvers)
        
    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, VerifyType.Definition), 'Invalid definition %s' % definition
        if not definition.solicitation: return False
        assert isinstance(definition.solicitation, VerifyType.Solicitation), \
        'Invalid solicitation %s' % definition.solicitation
        inp = definition.solicitation.input
        if not inp: return False
        assert isinstance(inp, Input), 'Invalid input %s' % inp
        if not self.check(self.type, inp.type): return False
        
        if self.info and not VerifyInfo.isValid(self, definition): return False
        return True
    
class VerifyProperty(VerifyInfo):
    '''
    Extension for a @see: VerifyInfo that validates for also for a specific property type.
    '''
    
    class Solicitation(Context):
        '''
        The solicitation context.
        '''
        # ---------------------------------------------------------------- Required
        property = requires(TypeProperty)
    
    def __init__(self, the, *info):
        '''
        Construct the info trigger.
        @see: VerifyInfo.__init__
        
        @param the: TypeProperty container
            The property type to check for.
        '''
        the = typeFor(the)
        assert isinstance(the, TypeProperty), 'Invalid property %s' % the
        if info: VerifyInfo.__init__(self, *info)
        else: self.info = None
        
        self.type = the
        
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Definition=VerifyType.Definition, Solicitation=VerifyProperty.Solicitation))
        if self.info: VerifyInfo.prepare(self, resolvers)
        
    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, VerifyType.Definition), 'Invalid definition %s' % definition
        if not definition.solicitation: return False
        assert isinstance(definition.solicitation, VerifyProperty.Solicitation), \
        'Invalid solicitation %s' % definition.solicitation
        if not isCompatible(self.type, definition.solicitation.property): return False
        
        if self.info and not VerifyInfo.isValid(self, definition): return False
        return True
    
class VerifyModelId(VerifyInfo):
    '''
    Extension for a @see: VerifyInfo that validates for model id properties types.
    '''
    
    def __init__(self, *info):
        '''
        Construct the info trigger.
        @see: VerifyInfo.__init__
        
        @param the: TypeProperty container
            The property type to check for.
        '''
        if info: VerifyInfo.__init__(self, *info)
        else: self.info = None
        
    def prepare(self, resolvers):
        '''
        @see: IVerifier.prepare
        '''
        merge(resolvers, dict(Solicitation=VerifyProperty.Solicitation))
        if self.info: VerifyInfo.prepare(self, resolvers)
        
    def isValid(self, definition):
        '''
        @see: IVerifier.isValid
        '''
        assert isinstance(definition, VerifyType.Definition), 'Invalid definition %s' % definition
        if not definition.solicitation: return False
        assert isinstance(definition.solicitation, VerifyProperty.Solicitation), \
        'Invalid solicitation %s' % definition.solicitation
        prop = definition.solicitation.property
        if not isinstance(prop, TypeProperty): return False
        assert isinstance(prop, TypeProperty)
        if not isinstance(prop.parent, TypeModel): return False
        assert isinstance(prop.parent, TypeModel)
        
        if prop.parent.propertyId != prop: return False
        
        if self.info and not VerifyInfo.isValid(self, definition): return False
        return True
