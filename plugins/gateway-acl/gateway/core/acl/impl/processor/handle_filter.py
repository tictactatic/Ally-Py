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
from ally.design.processor.attribute import requires, defines, optional
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

class ACLAllowed(Context):
    '''
    The ACL allowed context.
    '''
    # ---------------------------------------------------------------- Defined
    filters = defines(dict, doc='''
    @rtype: dictionary{Context: set(Context)}
    As a key the ACL filter context and as a value the path nodes to be filtered.
    ''')
    
class ACLFilter(Context):
    '''
    The ACL filter context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
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
    # ---------------------------------------------------------------- Optional
    filterHint = optional(str)
    # ---------------------------------------------------------------- Required
    action = requires(str)
    target = requires(object)
    access = requires(Context)
    method = requires(Context)
    allowed = requires(Context)
    forFilter = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='handleFilter')
class HandleFilter(HandlerProcessor):
    '''
    Implementation for a processor that provides the filters handling.
    '''
    
    def __init__(self):
        super().__init__(ACLAccess=ACLAccess, ACLMethod=ACLMethod, ACLAllowed=ACLAllowed, ACLFilter=ACLFilter)

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
                
            elif solicit.allowed:
                assert isinstance(solicit.allowed, ACLAllowed), 'Invalid allowed %s' % solicit.allowed
                if not solicit.allowed.filters: return
                
                names = (aclFilter.name for aclFilter in solicit.allowed.filters)
                if solicit.target == Filter: values = (self.create(name) for name in names)
                else: values = names
                if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
                else: solicit.value = values
                
            else:
                if solicit.target == Filter: values = (self.create(name) for name in register.filters)
                else: values = register.filters.keys()
                if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
                else: solicit.value = values
        
        elif solicit.action in (ACTION_ADD, ACTION_DEL):
            if solicit.target != Filter or not solicit.allowed or not solicit.forFilter: return chain.cancel()
            assert isinstance(solicit.allowed, ACLAllowed), 'Invalid allowed %s' % solicit.allowed
            assert isinstance(solicit.method, ACLMethod), 'Invalid method %s' % solicit.method
            assert isinstance(solicit.access, ACLAccess), 'Invalid access %s' % solicit.access
            
            aclFilter = register.filters[solicit.forFilter]
            
            if solicit.action == ACTION_ADD:
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
                if len(nodes) > 1:
                    if not Solicit.filterHint in solicit or not solicit.filterHint: return chain.cancel()
                    assert isinstance(solicit.filterHint, str), 'Invalid filter hint %s' % solicit.filterHint
                    markers = solicit.filterHint.strip('/').split('/')
                    if len(solicit.access.path) != len(markers): return chain.cancel()  # Not a correct path hint.
                    nodes = []
                    for el, mark in zip(solicit.access.path, markers):
                        if not isinstance(el, str):
                            if mark == '#': nodes.append(el)
                            elif mark != '*': return chain.cancel()  # Not a correct path.
                        elif el != mark: return chain.cancel()  # Not a correct path.
                        
                    if not nodes: return chain.cancel()
                
                if solicit.allowed.filters is None: solicit.allowed.filters = {}
                filterNodes = solicit.allowed.filters.get(aclFilter)
                if filterNodes is None: filterNodes = solicit.allowed.filters[aclFilter] = set()
                filterNodes.update(nodes)
            else:
                if not solicit.allowed.filters: return chain.cancel()
                if aclFilter not in solicit.allowed.filters: return chain.cancel()
                solicit.filters.pop(aclFilter)

    # ----------------------------------------------------------------
    
    def create(self, name):
        '''
        Create the filter.
        '''
        value = Filter()
        value.Name = name
        
        return value
