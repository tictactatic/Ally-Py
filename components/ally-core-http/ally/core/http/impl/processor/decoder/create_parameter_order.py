'''
Created on Jul 24, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the queries ascending and descending order criteria decoding.
'''

from .create_parameter import Parameter
from ally.api.type import List, Type
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.support.util_spec import IDo

# --------------------------------------------------------------------

NAME_ASC = 'asc'
# The name used for the ascending list of names.
NAME_DESC = 'desc'
# The name used for the descending list of names.

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create context.
    '''
    # ---------------------------------------------------------------- Required
    orderSetters = requires(dict)
    orderPrioritySetters = requires(dict)
    orderPriorityGetters = requires(list)
    
class DecodingOrder(Context):
    '''
    The order decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    doDecode = defines(IDo, doc='''
    @rtype: callable(target, value)
    Decodes the value into the provided target.
    @param target: Context
        Target context object used for decoding.
    @param value: object
        The value to be decoded.
    ''')
    type = defines(Type)
    
class DefinitionOrder(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    enumeration = defines(list, doc='''
    @rtype: list[string]
    The enumeration values that are allowed for order.
    ''')

class Target(Context):
    '''
    The target context.
    '''
    # ---------------------------------------------------------------- Required
    doFailure = requires(IDo)
      
# --------------------------------------------------------------------

@injected
class CreateParameterOrderDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the query order criterias decoding.
    '''
    
    decodeOrderAssembly = Assembly
    # The decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.decodeOrderAssembly, Assembly), \
        'Invalid order decode assembly %s' % self.decodeOrderAssembly
        super().__init__(Branch(self.decodeOrderAssembly).using(parameter=Parameter).
                         included(('decoding', 'Decoding')).included(), Target=Target)
        
    def process(self, chain, processing, create:Create, Decoding:DecodingOrder, Definition:DefinitionOrder, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the order decode.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert issubclass(Decoding, DecodingOrder), 'Invalid decoding class %s' % Decoding
        assert issubclass(Definition, DefinitionOrder), 'Invalid definition class %s' % Definition
        
        if not create.orderSetters: return 
        # There is not order to process.
        
        adec, ddec = Decoding(), Decoding()
        assert isinstance(adec, DecodingOrder), 'Invalid decoding %s' % adec
        assert isinstance(ddec, DecodingOrder), 'Invalid decoding %s' % ddec
        
        adec.type = ddec.type = List(str)
        
        
        adec.doDecode = self.createDecode(True, create.orderSetters, create.orderPriorityGetters,
                                          create.orderPrioritySetters, adec)
        ddec.doDecode = self.createDecode(False, create.orderSetters, create.orderPriorityGetters,
                                          create.orderPrioritySetters, ddec)
        
        adef = Definition(enumeration=sorted(create.orderSetters.keys()))
        ddef = Definition(enumeration=sorted(create.orderSetters.keys()))
        
        processing.wingIn(chain, True, decoding=ddec, definition=ddef, parameter=processing.ctx.parameter(path=[NAME_DESC]))
        processing.wingIn(chain, True, decoding=adec, definition=adef, parameter=processing.ctx.parameter(path=[NAME_ASC]))

    # ----------------------------------------------------------------
    
    def createDecode(self, asc, settersAsc, gettersPriority, settersPriority, decoding):
        '''
        Create the order do decode.
        '''
        assert isinstance(asc, bool), 'Invalid ascending flag %s' % asc
        assert isinstance(settersAsc, dict), 'Invalid ascending mapping %s' % settersAsc
        assert isinstance(gettersPriority, list), 'Invalid priority getters %s' % gettersPriority
        assert isinstance(settersPriority, dict), 'Invalid priority setter %s' % settersPriority
        def doDecode(target, value):
            '''
            Do the order decode.
            '''
            assert isinstance(target, Target), 'Invalid target %s' % target
            
            if not isinstance(value, list): return target.doFailure(decoding, value)
            
            for item in value:
                setAsc = settersAsc.get(item)
                if setAsc is None: target.doFailure(decoding, item)
                else:
                    setAsc(target, asc)
                    setPriority = settersPriority.get(item)
                    if setPriority:
                        priorities = [priority for priority in (getPriority(target) for getPriority in gettersPriority)
                                      if priority is not None]
                        if priorities: current = max(priorities)
                        else: current = 0
                        
                        setPriority(target, current + 1)
        return doDecode
