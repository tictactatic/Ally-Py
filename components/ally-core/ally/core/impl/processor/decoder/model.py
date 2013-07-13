'''
Created on Jul 11, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the model decoding.
'''

from ally.api.operator.type import TypeProperty, TypeModel
from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IDevise
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create decoder context.
    ''' 
    # ---------------------------------------------------------------- Required
    solicitations = requires(list)

class SolicitationModel(Context):
    '''
    The decoder solicitation context.
    '''
    # ---------------------------------------------------------------- Defined
    solicitation = defines(Context)
    path = defines(str)
    property = defines(TypeProperty)
    devise = defines(IDevise)
    objType = defines(Type)
    solicitation = defines(Context, doc='''
    @rtype: Context
    The solicitation that this solicitation is based on.
    ''')
    
# --------------------------------------------------------------------

@injected
class ModelDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the model values decoding.
    '''
    
    separator = str
    # The separator to be used for path.
    
    def __init__(self):
        assert isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__()
        
    def process(self, chain, create:Create, Solicitation:SolicitationModel, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the model solicitation decode.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Solicitation, SolicitationModel), 'Invalid solicitation class %s' % Solicitation
        
        if not create.solicitations: return 
        # There is not solicitation to process.
        
        k, solicitations = 0, []
        while k < len(create.solicitations):
            sol = create.solicitations[k]
            k += 1
            
            assert isinstance(sol, SolicitationModel), 'Invalid solicitation %s' % sol
            
            if not isinstance(sol.objType, TypeModel): continue
            # If the type is not model just move along.
            assert isinstance(sol.objType, TypeModel)
            
            k -= 1
            del create.solicitations[k]
        
            names = sorted(sol.objType.properties)
            names.sort(key=lambda pname: len(pname))
            for pname, prop in zip(names, map(sol.objType.properties.get, names)):
                assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
                assert isinstance(prop.parent, TypeModel), 'Invalid model property %s' % prop.parent
                
                psol = Solicitation()
                solicitations.append(psol)
                assert isinstance(psol, SolicitationModel), 'Invalid solicitation %s' % psol
                
                psol.solicitation = sol
                psol.path = self.separator.join((prop.parent.name, pname))
                psol.property = prop
                psol.devise = DeviseProperty(sol.devise, prop)
                psol.objType = prop.type
                psol.solicitation = sol
                
        if solicitations: create.solicitations.extend(solicitations)

# --------------------------------------------------------------------

class DeviseProperty(IDevise):
    '''
    Implementation for @see: IDevise for handling model properties.
    '''
    
    def __init__(self, devise, property):
        '''
        Construct the devise for model property.
        '''
        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
        assert isinstance(property, TypeProperty), 'Invalid property %s' % property
        assert isinstance(property.parent, TypeModel), 'Invalid model property %s' % property
        
        self.devise = devise
        self.property = property
        
    def get(self, target):
        '''
        @see: IDevise.get
        '''
        model = self.devise.get(target)
        if model is None: return
        return getattr(model, self.property.name)
        
    def set(self, target, value, support):
        '''
        @see: IDevise.set
        '''
        model = self.devise.get(target)
        if model is None:
            model = self.property.parent.clazz()
            self.devise.set(target, model, support)
        setattr(model, self.property.name, value)
