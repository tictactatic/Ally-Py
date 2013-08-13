'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the filter handling.
'''

from ..base import ACTION_GET, ACTION_ADD, ACTION_DEL
from ally.api.operator.type import TypeProperty
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.filter import Filter
import itertools

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    filters = requires(dict)
    
class ACLAccess(Context):
    '''
    The ACL access context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(list)
    
class ACLMethod(Context):
    '''
    The ACL method context.
    '''
    # ---------------------------------------------------------------- Required
    nodesProperties = requires(dict)

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
    access = requires(Context)
    method = requires(Context)
    filters = requires(dict)
    forFilter = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='handleFilter')
class HandleFilter(HandlerProcessor):
    '''
    Implementation for a processor that provides the filters handling.
    '''
    
    def __init__(self):
        super().__init__(ACLAccess=ACLAccess, ACLMethod=ACLMethod, ACLFilter=ACLFilter)

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
        if solicit.target not in (Filter, Filter.Name): return
        
        if solicit.action == ACTION_GET:
            if solicit.forFilter:
                if solicit.target == Filter: solicit.value = self.create(solicit.forFilter)
                else: solicit.value = solicit.forFilter
                
            elif solicit.filters is not None:
                if not solicit.filters: return
                
                if solicit.target == Filter: values = (self.create(name) for name in solicit.filters)
                else: values = solicit.filters.keys()
                if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
                else: solicit.value = values
                
            else:
                if solicit.target == Filter: values = (self.create(name) for name in register.filters)
                else: values = register.filters.keys()
                if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
                else: solicit.value = values
        
        elif solicit.action in (ACTION_ADD, ACTION_DEL):
            if solicit.target != Filter or solicit.filters is None or not solicit.forFilter: return chain.cancel()
            assert isinstance(solicit.method, ACLMethod), 'Invalid method %s' % solicit.method
            assert isinstance(solicit.access, ACLAccess), 'Invalid access %s' % solicit.access
            
            if solicit.action == ACTION_ADD:
                aclFilter = register.filters[solicit.forFilter]
                assert isinstance(aclFilter, ACLFilter), 'Invalid filter %s' % aclFilter
                assert isinstance(aclFilter.targetProperty, TypeProperty), \
                'Invalid target property %s' % aclFilter.targetProperty
                assert isinstance(solicit.method.nodesProperties, dict), \
                'Invalid nodes properties %s' % solicit.method.nodesProperties
                
                nodes = []
                for el in solicit.access.path:
                    if not isinstance(el, str):
                        prop = solicit.method.nodesProperties.get(el)
                        if prop == aclFilter.targetProperty: nodes.append(el)
                
                if not nodes: return chain.cancel()
                if len(nodes) > 1: return chain.cancel()  # TODO: Gabriel: implement filter pattern.
                
                solicit.filters[solicit.forFilter] = (aclFilter, nodes[0])
            else:
                if not solicit.filters: return chain.cancel()
                if solicit.forFilter not in solicit.filters: return chain.cancel()
                solicit.filters.pop(solicit.forFilter)

    # ----------------------------------------------------------------
    
    def create(self, name):
        '''
        Create the filter.
        '''
        value = Filter()
        value.Name = name
        
        return value
