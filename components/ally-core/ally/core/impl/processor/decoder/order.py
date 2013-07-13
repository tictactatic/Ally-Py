'''
Created on Jun 19, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the queries ascending and descending order criteria decoding.
'''

from ally.api.criteria import AsOrdered
from ally.api.operator.type import TypeProperty
from ally.api.type import Type, List, typeFor
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IDevise
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.support.api.util_service import isCompatible

# --------------------------------------------------------------------

class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    enumeration = defines(list, doc='''
    @rtype: list[string]
    The enumeration values that are allowed for order.
    ''')
    # ---------------------------------------------------------------- Required
    solicitation = requires(Context)

class Create(Context):
    '''
    The create decoder context.
    '''
    # ---------------------------------------------------------------- Defined
    decoders = defines(list)
    definitions = defines(list)
    # ---------------------------------------------------------------- Required
    solicitations = requires(list)
    
class Support(Context):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Defined
    failures = defines(list)

class CreateOrder(Context):
    '''
    The create order decoder context.
    '''
    # ---------------------------------------------------------------- Defined
    solicitations = defines(list)
    # ---------------------------------------------------------------- Required
    decoders = requires(list)
    definitions = requires(list)

class SolicitationOrder(Context):
    '''
    The decoder solicitation context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(str)
    objType = defines(Type)
    # ---------------------------------------------------------------- Required
    pathRoot = requires(str)
    devise = requires(IDevise)
    property = requires(TypeProperty)
    
# --------------------------------------------------------------------

@injected
class OrderDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the query order criterias decoding.
    '''
    
    orderAssembly = Assembly
    # The order decode processors to be used for decoding.
    nameAsc = 'asc'
    # The name used for the ascending list of names.
    nameDesc = 'desc'
    # The name used for the descending list of names.
    
    def __init__(self):
        assert isinstance(self.orderAssembly, Assembly), 'Invalid order assembly %s' % self.orderAssembly
        assert isinstance(self.nameAsc, str), 'Invalid name for ascending %s' % self.nameAsc
        assert isinstance(self.nameDesc, str), 'Invalid name for descending %s' % self.nameDesc
        super().__init__(Branch(self.orderAssembly).using(create=CreateOrder).included(),
                         Definition=Definition, Support=Support)
        
    def process(self, chain, processing, create:Create, Solicitation:SolicitationOrder, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the order decode.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Solicitation, SolicitationOrder), 'Invalid solicitation class %s' % Solicitation
        
        if not create.solicitations: return 
        # There is not solicitation to process.
        
        keyargs.update(Solicitation=Solicitation)
        
        k, ascending, priority = 0, {}, {}
        while k < len(create.solicitations):
            sol = create.solicitations[k]
            k += 1
            
            assert isinstance(sol, SolicitationOrder), 'Invalid solicitation %s' % sol
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
            del create.solicitations[k]
            
        if ascending:
            sola, sold = Solicitation(), Solicitation()
            assert isinstance(sola, SolicitationOrder), 'Invalid solicitation %s' % sola
            assert isinstance(sold, SolicitationOrder), 'Invalid solicitation %s' % sold
            
            sola.devise = DeviseOrder(self.nameAsc, True, ascending, priority)
            sola.path = self.nameAsc
            
            sold.devise = DeviseOrder(self.nameDesc, False, ascending, priority)
            sold.path = self.nameDesc
            
            sola.objType = sold.objType = typeFor(List(str))
            
            arg = processing.execute(create=processing.ctx.create(solicitations=[sola, sold]), **keyargs)
            assert isinstance(arg.create, CreateOrder), 'Invalid create %s' % arg.create
            
            if arg.create.decoders:
                if create.decoders is None: create.decoders = arg.create.decoders
                else: create.decoders.extend(arg.create.decoders)
            if arg.create.definitions:
                enumeration = sorted(ascending.keys())
                for defin in arg.create.definitions:
                    assert isinstance(defin, Definition), 'Invalid definition %s' % defin
                    if defin.solicitation in (sola, sold): defin.enumeration = enumeration
                        
                if create.definitions is None: create.definitions = arg.create.definitions
                else: create.definitions.extend(arg.create.definitions)

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
