'''
Created on Jun 19, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the queries ascending and descending order criteria decoding.
'''

from ally.api.criteria import AsOrdered
from ally.api.operator.type import TypeQuery, TypeProperty, TypeCriteria, \
    TypeModel, TypeContainer
from ally.api.type import Type, List, typeFor
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IDevise, IDecoder
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.api.util_service import isCompatible
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

class DefinitionOrder(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str)
    enumeration = defines(list, doc='''
    @rtype: list[string]
    The enumeration values that are allowed for order.
    ''')
    description = defines(list)

class Create(Context):
    '''
    The create decoder context.
    '''
    # ---------------------------------------------------------------- Required
    solicitaions = requires(list)
    definition = requires(Context)
                   
class SolicitaionOrder(Context):
    '''
    The decoder solicitaion context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(object)
    objType = defines(Type)
    key = defines(frozenset)
    definition = defines(Context)
    # ---------------------------------------------------------------- Required
    pathRoot = requires(object)
    devise = requires(IDevise)
    property = requires(TypeProperty)

class Support(Context):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Defined
    failures = defines(list)
    
# --------------------------------------------------------------------

@injected
class OrderDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the query order criterias decoding.
    '''
    
    nameAsc = 'asc'
    # The name used for the ascending list of names.
    nameDesc = 'desc'
    # The name used for the descending list of names.
    
    def __init__(self):
        assert isinstance(self.nameAsc, str), 'Invalid name for ascending %s' % self.nameAsc
        assert isinstance(self.nameDesc, str), 'Invalid name for descending %s' % self.nameDesc
        super().__init__(Support=Support)
        
    def process(self, chain, invoker:Invoker, Definition:DefinitionOrder, create:Create,
                Solicitaion:SolicitaionOrder, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the order decode.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Definition, DefinitionOrder), 'Invalid definition class %s' % Definition
        assert issubclass(Solicitaion, SolicitaionOrder), 'Invalid solicitaion class %s' % Solicitaion
        
        if not create.solicitaions: return 
        # There is not solicitaion to process.
        
        k, ascending, priority = 0, {}, {}
        while k < len(create.solicitaions):
            sol = create.solicitaions[k]
            k += 1
            
            assert isinstance(sol, Solicitaion), 'Invalid solicitation %s' % sol
            if not sol.pathRoot or not sol.property: continue
            
            if isCompatible(AsOrdered.ascending, sol.property):
                assert isinstance(sol.devise, IDevise), 'Invalid devise %s' % sol.devise
                ascending[sol.pathRoot] = sol.devise
            elif isCompatible(AsOrdered.priority, sol.property):
                assert isinstance(sol.devise, IDevise), 'Invalid devise %s' % sol.devise
                priority[sol.pathRoot] = sol.devise
            else: continue
            # Is not an ordered criteria.
            
            k -= 1
            del create.solicitaions[k]
            
        if ascending:
            sola, sold = Solicitaion(), Solicitaion()
            assert isinstance(sola, SolicitaionOrder), 'Invalid solicitation %s' % sola
            assert isinstance(sold, SolicitaionOrder), 'Invalid solicitation %s' % sold
            create.solicitaions.append(sola)
            create.solicitaions.append(sold)
            
            sola.devise = DeviseOrder(self.nameAsc, True, ascending, priority)
            sola.key = frozenset((self.nameAsc,))
            sola.path = self.nameAsc
            
            sold.devise = DeviseOrder(self.nameDesc, False, ascending, priority)
            sold.key = frozenset((self.nameDesc,))
            sold.path = self.nameDesc
            
            sola.objType = sold.objType = typeFor(List(str))
            sola.definition = sold.definition = create.definition
            
            if invoker.definitions is None: invoker.definitions = {}
            defa, defd = Definition(), Definition()
            assert isinstance(defa, DefinitionOrder), 'Invalid definition %s' % defa
            assert isinstance(defd, DefinitionOrder), 'Invalid definition %s' % defd
            
            defa.name = self.nameAsc
            defa.description = ['provide the names that you want to order by ascending',
                                'the order in which the names are provided establishes the order priority']
            invoker.definitions[sola.key] = defa
            
            defd.name = self.nameDesc
            defd.description = ['provide the names that you want to order by descending',
                                'the order in which the names are provided establishes the order priority']
            invoker.definitions[sold.key] = defd
            
            defa.enumeration = defd.enumeration = sorted(ascending.keys())

# --------------------------------------------------------------------

class DeviseOrder(IDevise):
    '''
    Implementation for a @see: IDevise for queries order.
    '''
    
    def __init__(self, name, asc, ascending, priority):
        '''
        Construct the order decoder.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(asc, bool), 'Invalid ascending flag %s' % asc
        assert isinstance(ascending, dict), 'Invalid ascending mapping %s' % ascending
        assert isinstance(priority, dict), 'Invalid priority mapping %s' % priority
        
        self.name = name
        self.asc = asc
        self.ascending = ascending
        self.priority = priority
    
    def get(self, target):
        '''
        @see: IDevise.get
        '''
        return None
    
    def set(self, target, value, support):
        '''
        @see: IDevise.set
        '''
        assert isinstance(value, list), 'Invalid value %s' % value
        assert isinstance(support, Support), 'Invalid support %s' % support
        for item in value:
            ascending = self.ascending.get(item)
            if ascending is None:
                if support.failures is None: support.failures = []
                support.failures.append('Unknown name \'%s\' for \'%s\'' % (item, self.name))
            else:
                assert isinstance(ascending, IDevise), 'Invalid devise %s' % ascending
                ascending.set(target, self.asc, support)
                priority = self.priority.get(item)
                if priority:
                    assert isinstance(priority, IDevise), 'Invalid devise %s' % priority
                    current = 0
                    for devise in self.priority.values():
                        assert isinstance(devise, IDevise), 'Invalid devise %s' % devise
                        val = devise.get(target)
                        if val is not None: current = max(current, val)
                    
                    priority.set(target, current + 1, support)
