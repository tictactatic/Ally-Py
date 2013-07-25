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
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor
from ally.support.api.util_service import isCompatible
from ally.support.util_spec import IDo

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create context.
    '''
    # ---------------------------------------------------------------- Defined
    orderSetters = defines(dict, doc='''
    @rtype: dictionary{string: callable(@see: decoding.doSet)}
    The order setters indexed by the full name.
    ''')
    orderPrioritySetters = defines(dict, doc='''
    @rtype: dictionary{string: callable(@see: decoding.doSet)}
    The order priority setters indexed by the full name.
    ''')
    orderPriorityGetters = defines(list, doc='''
    @rtype: list[callable(@see: decoding.doGet)]
    The order priority getters.
    ''')
    
class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Required
    property = requires(TypeProperty)
    doSet = requires(IDo)
    doGet = requires(IDo)

class Parameter(Context):
    '''
    The parameter context.
    '''
    # ---------------------------------------------------------------- Defined
    path = requires(list)
    
# --------------------------------------------------------------------

@injected
class OrderDecode(HandlerProcessor):
    '''
    Implementation for a handler that provides the query order criterias decoding.
    '''
    
    separator = '.'
    # The separator to use for parameter names.
    
    def __init__(self):
        assert isinstance(self.separator, str), 'Invalid separator %s' % self.separator
        super().__init__()
        
    def process(self, chain, create:Create, decoding:Decoding, parameter:Parameter, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the order decode.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(parameter, Parameter), 'Invalid parameter %s' % parameter
        
        if not decoding.property: return
        
        if isCompatible(AsOrdered.ascending, decoding.property):
            assert isinstance(decoding.doSet, IDo), 'Invalid do set %s' % decoding.doSet
            assert parameter.path, 'Invalid parameter path %s' % parameter
            
            if create.orderSetters is None: create.orderSetters = {}
            create.orderSetters[self.separator.join(parameter.path[:-1])] = decoding.doSet
            chain.cancel()  # Cancel the decode creation
        elif isCompatible(AsOrdered.priority, decoding.property):
            assert isinstance(decoding.doSet, IDo), 'Invalid do set %s' % decoding.doSet
            assert isinstance(decoding.doGet, IDo), 'Invalid do get %s' % decoding.doGet
            assert parameter.path, 'Invalid parameter path %s' % parameter
            
            if create.orderPrioritySetters is None: create.orderPrioritySetters = {}
            if create.orderPriorityGetters is None: create.orderPriorityGetters = []
            create.orderPrioritySetters[self.separator.join(parameter.path[:-1])] = decoding.doSet
            create.orderPriorityGetters.append(decoding.doGet)
            chain.cancel()  # Cancel the decode creation
