'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the filter handling.
'''

from ally.api.operator.type import TypeProperty
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.filter import Filter
from gateway.api.group import Group
from gateway.core.acl.spec import ACTION_GET, ACTION_ADD, ACTION_DEL
import itertools

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    filters = requires(dict)
    
class ACLMethod(Context):
    '''
    The ACL method context.
    '''
    # ---------------------------------------------------------------- Defined
    filters = defines(dict, doc='''
    @rtype: dictionary{string: dictionary{string: tuple(Context, Context)}}
    Contains as value a dictionary having as the key the filter name and as a value a tuple having on the first position
    the filter context and on the second the access path node that they are filtering. The values dictionaries are
    indexed by the allowed group name.
    ''')

class ACLFilter(Context):
    '''
    The ACL filter context.
    '''
    # ---------------------------------------------------------------- Required
    targetProperty = requires(TypeProperty)
   
class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    value = defines(object, doc='''
    @rtype: object
    The value required.
    ''')
    # ---------------------------------------------------------------- Required
    action = requires(str)
    target = requires(object)
    method = requires(Context)
    forGroup = requires(str)
    forFilter = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='handleFilter')
class HandleFilter(HandlerProcessor):
    '''
    Implementation for a processor that provides the filters handling.
    '''
    
    def __init__(self):
        super().__init__(ACLMethod=ACLMethod, ACLFilter=ACLFilter)

    def process(self, chain, register:Register, solicit:Solicit, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the filter handling.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        
        if solicit.forFilter is not None:
            if not register.filters or solicit.forFilter not in register.filters: return chain.cancel()
            
        if solicit.action == ACTION_GET:
            if solicit.target not in (Filter, Filter.Name): return
            
            if solicit.forFilter:
                if solicit.target == Filter: solicit.value = self.create(solicit.forFilter)
                else: solicit.value = solicit.forFilter
                
            elif solicit.forGroup:
                if not solicit.method or not solicit.method.filters: return chain.cancel()
                assert isinstance(solicit.method, ACLMethod), 'Invalid method %s' % solicit.method
                filters = solicit.method.filters.get(solicit.forGroup)
                if not filters: return chain.cancel()
                
                if solicit.target == Filter: values = (self.create(name) for name in filters)
                else: values = filters.keys()
                if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
                else: solicit.value = values
                
            else:
                if solicit.target == Filter: values = (self.create(name) for name in register.filters)
                else: values = register.filters.keys()
                if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
                else: solicit.value = values
        
        elif solicit.action in (ACTION_ADD, ACTION_DEL):
            if solicit.target != Filter:
                if solicit.target == Group and solicit.method and solicit.forGroup:
                    if solicit.method.filters and solicit.forGroup in solicit.method.filters:
                        solicit.method.filters.pop(solicit.forGroup)
                return
            
            if not solicit.method or not solicit.forGroup or not solicit.forFilter: return chain.cancel()
            assert isinstance(solicit.method, ACLMethod), 'Invalid method %s' % solicit.method
            
            if solicit.action == ACTION_ADD:
                filter = register.filters[solicit.forFilter]
                assert isinstance(filter, ACLFilter), 'Invalid filter %s' % filter
                
                if solicit.method.filters is None: solicit.method.filters = {}
                filters = solicit.method.filters.get(solicit.forGroup)
                if filters is None: filters = solicit.method.filters[solicit.forGroup] = {}
                filters[solicit.forFilter] = (filter, None)  # TODO: add node
            else:
                if not solicit.method.filters or solicit.forGroup not in solicit.method.filters: return chain.cancel()
                filters = solicit.method.filters[solicit.forGroup]
                if solicit.forFilter not in filters: return chain.cancel()
                filters.pop(solicit.forFilter)

    # ----------------------------------------------------------------
    
    def create(self, name):
        '''
        Create the filter.
        '''
        value = Filter()
        value.Name = name
        
        return value
