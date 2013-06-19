'''
Created on Jun 18, 2013

@package: ally core http
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
from inspect import getdoc
from timeit import itertools

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    definitions = defines(dict)
    # ---------------------------------------------------------------- Required
    target = requires(TypeModel)

class DefinitionQuery(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    parent = defines(Context)
    description = defines(list)

class Create(Context):
    '''
    The create decoder context.
    '''
    # ---------------------------------------------------------------- Defined
    solicitaions = defines(list)
                   
class Solicitaion(Context):
    '''
    The decoder solicitaion context.
    '''
    # ---------------------------------------------------------------- Defined
    pathRoot = defines(object, doc='''
    @rtype: object
    The root of the path.
    ''')
    path = defines(object)
    devise = defines(IDevise)
    property = defines(TypeProperty, doc='''
    @rtype: TypeProperty
    The property that represents the solicitaion.
    ''')
    objType = defines(Type)
    key = defines(frozenset)
    definition = defines(Context)
    
# --------------------------------------------------------------------

@injected
class QueryDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the query values decoding.
    '''
    
    def __init__(self):
        super().__init__(Solicitaion=Solicitaion)
        
    def process(self, chain, invoker:Invoker, Definition:DefinitionQuery, create:Create, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the query solicitation decode.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert issubclass(Definition, DefinitionQuery), 'Invalid definition class %s' % Definition
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if not create.solicitaions: return 
        # There is not solicitaion to process.
        
        k, solicitaions = 0, []
        while k < len(create.solicitaions):
            sol = create.solicitaions[k]
            k += 1
            
            assert isinstance(sol, Solicitaion), 'Invalid solicitation %s' % sol
            
            if not isinstance(sol.objType, TypeQuery): continue
            # If the type is not query just move along.
            assert isinstance(sol.objType, TypeQuery)
            
            k -= 1
            del create.solicitaions[k]
        
            definition = Definition(parent=sol.definition, description=[])
            assert isinstance(definition, DefinitionQuery), 'Invalid definition %s' % definition
            if __debug__:  # In debug mode we might find some documentation on the query class
                definition.description.append(getdoc(sol.objType.clazz).strip())
            definition.description.append('The available parameters based on query')
        
            # If the query is for the target model then we will use simple names.
            if invoker.target == sol.objType.target: qpath = '' 
            else: qpath = sol.path
        
            for cname, cprop in sol.objType.properties.items():
                assert isinstance(cprop, TypeProperty), 'Invalid property %s' % cprop
                assert isinstance(cprop.type, TypeCriteria), 'Invalid criteria %s' % cprop.type
                
                if qpath: cpath = '%s.%s' % (qpath, cname)
                else: cpath = cname
                
                pathByName, data = {}, dict(pathRoot=cpath, definition=definition)
                for name, prop in cprop.type.properties.items():
                    assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
                    path = pathByName[name] = '%s.%s' % (cpath, name)
                    solicitaions.append(sol.__class__(path=path,
                                                      devise=DeviseCriteria(sol.devise, cprop, prop),
                                                      property=prop, objType=prop.type,
                                                      key=frozenset(itertools.chain(sol.key, (cprop, prop))),
                                                      **data))
                
                if cprop.type.main:
                    prop = firstOf(cprop.type.main.values())
                    key = frozenset(itertools.chain(sol.key, (cprop,)))
                    solicitaions.append(sol.__class__(path=cpath,
                                                      devise=DeviseCriteria(sol.devise, cprop, *cprop.type.main.values()),
                                                      property=prop, objType=prop.type,
                                                      key=key,
                                                      **data))
                    if invoker.definitions is None: invoker.definitions = {}
                    invoker.definitions[key] = Definition(parent=definition, description=[
                    'will automatically set the value to %s' % \
                    ', '.join(pathByName[name] for name in cprop.type.main if name in pathByName)])
                    
        create.solicitaions.extend(solicitaions)

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
