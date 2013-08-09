'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the filter names and objects.
'''

from . import get_method
from ally.container.support import setup
from ally.design.processor.attribute import requires
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
    access = requires(dict)
    filters = requires(dict)

class Access(Context):
    '''
    The access context.
    '''
    # ---------------------------------------------------------------- Required
    permissions = requires(dict)

class Permission(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Required
    allowed = requires(dict)
    
class Get(get_method.Get):
    '''
    The get method context.
    '''
    # ---------------------------------------------------------------- Required
    forMethod = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='getFilter')
class GetFilter(HandlerProcessor):
    '''
    Implementation for a processor that provides the filters names and objects.
    '''
    
    def __init__(self):
        super().__init__(Access=Access)

    def process(self, chain, register:Register, get:Get=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the methods.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.filters or not register.access: return
        assert isinstance(register.filters, dict), 'Invalid access filters %s' % register.filters
        assert isinstance(register.access, dict), 'Invalid access %s' % register.access
        if not get: return
        assert isinstance(get, Get), 'Invalid get method %s' % get
        if get.target not in (Filter, Filter.Name): return
        
        if get.forName is not None:
            if get.forName not in register.filters: return chain.cancel()
            if get.target == Filter: get.value = self.create(get.forName)
            else: get.value = get.forName
        
        elif get.forAccess is not None:
            access = register.access.get(get.forAccess)
            if not access: return chain.cancel()
            assert isinstance(access, Access), 'Invalid access %s' % access
            if not access.permissions: return
            assert isinstance(access.permissions, dict), 'Invalid access permissions %s' % access.permissions
            if get.forMethod:
                permission = access.permissions.get(get.forMethod)
                if not permission: return chain.cancel()
                permissions = (permission,)
            else: permissions = access.permissions.values()
            
            names = set()
            for permission in permissions:
                assert isinstance(permission, Permission), 'Invalid permission %s' % permission
                if not permission.allowed: continue
                assert isinstance(permission.allowed, dict), 'Invalid permission allowed %s' % permission.allowed
                
                if get.forGroup:
                    filters = permission.allowed.get(get.forGroup)
                    if filters: names.update(filters)
                else:
                    for filters in permission.allowed.values(): names.update(filters)
                
            if get.target == Filter: values = (self.create(name) for name in names)
            else: values = names
            if get.value is not None: get.value = itertools.chain(get.names, values)
            else: get.value = values
            
        elif get.forAll:
            if get.target == Filter: values = (self.create(name) for name in register.filters)
            else: values = register.filters.keys()
            if get.value is not None: get.value = itertools.chain(get.value, values)
            else: get.value = values

    # ----------------------------------------------------------------
    
    def create(self, name):
        '''
        Create the filter.
        '''
        value = Filter()
        value.Name = name
        
        return value
