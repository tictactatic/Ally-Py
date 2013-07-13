'''
Created on Jun 18, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the queries types decoding.
'''

from ally.api.operator.type import TypeQuery, TypeProperty, TypeCriteria, \
    TypeModel
from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IDevise
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util import firstOf

# --------------------------------------------------------------------

INFO_CRITERIA_MAIN = 'criteria_main'
# The index for main criteria info.

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    target = requires(TypeModel)

class Create(Context):
    '''
    The create decoder context.
    '''
    # ---------------------------------------------------------------- Required
    solicitations = requires(list)

class SolicitationQuery(Context):
    '''
    The decoder solicitation context.
    '''
    # ---------------------------------------------------------------- Defined
    solicitation = defines(Context, doc='''
    @rtype: Context
    The solicitation that this solicitation is based on.
    ''')
    pathRoot = defines(str, doc='''
    @rtype: string
    The root of the path.
    ''')
    property = defines(TypeProperty, doc='''
    @rtype: TypeProperty
    The property that represents the solicitation.
    ''')
    info = defines(dict, doc='''
    @rtype: dictionary{string: object}
    Information related to the solictiation that can be used in constructing definitions descriptions.
    ''')
    # ---------------------------------------------------------------- Required
    path = requires(str)
    devise = requires(IDevise)
    objType = requires(Type)

# --------------------------------------------------------------------

@injected
class QueryDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the query values decoding.
    '''
    
    separator = str
    # The separator to be used for path.
    
    def __init__(self):
        assert isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__()
        
    def process(self, chain, invoker:Invoker, create:Create, Solicitation:SolicitationQuery, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the query solicitation decode.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Solicitation, SolicitationQuery), 'Invalid solicitation class %s' % Solicitation
        
        if not create.solicitations: return 
        # There is not solicitation to process.
        
        k, solicitations = 0, []
        while k < len(create.solicitations):
            sol = create.solicitations[k]
            k += 1
            
            assert isinstance(sol, SolicitationQuery), 'Invalid solicitation %s' % sol
            
            if not isinstance(sol.objType, TypeQuery): continue
            # If the type is not query just move along.
            assert isinstance(sol.objType, TypeQuery)
            
            k -= 1
            del create.solicitations[k]
        
            # If the query is for the target model then we will use simple names.
            if invoker.target == sol.objType.target: qpath = None
            else: qpath = sol.path
        
            for cname, cprop in sol.objType.properties.items():
                assert isinstance(cprop, TypeProperty), 'Invalid property %s' % cprop
                assert isinstance(cprop.type, TypeCriteria), 'Invalid criteria %s' % cprop.type
                
                if qpath: cpath = self.separator.join((qpath, cname,))
                else: cpath = cname
                
                pathByName = {}
                for name, prop in cprop.type.properties.items():
                    assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
                    csol = Solicitation()
                    solicitations.append(csol)
                    assert isinstance(csol, SolicitationQuery), 'Invalid solicitation %s' % csol
                    
                    csol.solicitation = sol
                    csol.path = pathByName[name] = self.separator.join((cpath , name))
                    csol.devise = DeviseCriteria(sol.devise, cprop, prop)
                    csol.property = prop
                    csol.objType = prop.type
                    csol.pathRoot = cpath
                
                if cprop.type.main:
                    msol = Solicitation()
                    solicitations.append(msol)
                    assert isinstance(msol, SolicitationQuery), 'Invalid solicitation %s' % msol
                    
                    msol.solicitation = sol
                    msol.path = cpath
                    msol.devise = DeviseCriteria(sol.devise, cprop, *cprop.type.main.values())
                    msol.objType = firstOf(cprop.type.main.values()).type
                    msol.pathRoot = cpath
                    msol.info = {INFO_CRITERIA_MAIN: [pathByName[name] for name in cprop.type.main if name in pathByName]}
                    
        if solicitations: create.solicitations.extend(solicitations)

# --------------------------------------------------------------------

class DeviseCriteria(IDevise):
    '''
    Implementation for @see: IDevise for handling criteria properties.
    '''
    
    def __init__(self, devise, criteria, *properties):
        '''
        Construct the devise criteria.
        '''
        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
        assert isinstance(criteria, TypeProperty), 'Invalid criteria property %s' % criteria
        assert properties, 'At least one property is required'
        if __debug__:
            for prop in properties: assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
        
        self.devise = devise
        self.criteria = criteria
        self.properties = properties
        
    def get(self, target):
        '''
        @see: IDevise.get
        '''
        query = self.devise.get(target)
        if query is None: return
        if self.criteria not in query: return
        return getattr(getattr(query, self.criteria.name), self.properties[0].name)
        
    def set(self, target, value, support):
        '''
        @see: IDevise.set
        '''
        query = self.devise.get(target)
        if query is None:
            query = self.criteria.parent.clazz()
            self.devise.set(target, query, support)
        target = getattr(query, self.criteria.name)
        for prop in self.properties:
            assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
            setattr(target, prop.name, value)
