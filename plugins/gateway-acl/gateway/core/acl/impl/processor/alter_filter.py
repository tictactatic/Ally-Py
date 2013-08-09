'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the access filters alteration.
'''

from . import alter_method
from ally.container.support import setup
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.filter import Filter

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
        
class Alter(alter_method.Alter):
    '''
    The alter method context.
    '''
    # ---------------------------------------------------------------- Required
    filter = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='alterFilter')
class AlterFilter(HandlerProcessor):
    '''
    Implementation for a processor that provides the access filters alteration.
    '''
    
    def __init__(self):
        super().__init__(Access=Access, Permission=Permission)

    def process(self, chain, register:Register, add:Alter=None, remove:Alter=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Alter the access filters.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        
        if add:
            assert isinstance(add, Alter), 'Invalid add filter %s' % add
            if add.target != Filter: return
            
            filters = self.filtersFor(register, add)
            if filters is None: return chain.cancel()
            assert isinstance(filters, dict), 'Invalid filters %s' % filters
            if add.filter in filters: return
            assert isinstance(add.filter, str), 'Invalid add filter %s' % add.filter
            if not register.filters: return chain.cancel()
            assert isinstance(register.filters, dict), 'Invalid filters %s' % register.filters
            filter = register.filters.get(add.filter)
            if not filter: return chain.cancel()
            filters[add.filter] = filter
            # TODO: Gabriel: add filter checking
            
        if remove:
            assert isinstance(remove, Alter), 'Invalid remove filter %s' % add
            if remove.target != Filter: return
            
            filters = self.filtersFor(register, remove)
            if filters is None or remove.filter not in filters: return chain.cancel()
            assert isinstance(filters, dict), 'Invalid filters %s' % filters
            filters.pop(remove.filter)

    # ----------------------------------------------------------------
    
    def filtersFor(self, register, alter):
        '''
        Provides the permission for the alter.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(alter, Alter), 'Invalid alter %s' % alter
        if not register.access: return
        assert isinstance(register.access, dict), 'Invalid access %s' % register.access
        
        access = register.access.get(alter.access)
        if not access: return
        assert isinstance(access, Access), 'Invalid access %s' % access
        assert isinstance(access.permissions, dict), 'Invalid permissions %s' % access.permissions
        permission = access.permissions.get(alter.method)
        if not permission: return
        assert isinstance(permission, Permission), 'Invalid permission %s' % permission
        if not permission.allowed: return
        assert isinstance(permission.allowed, dict), 'Invalid permission allowed %s' % permission.allowed 
        return permission.allowed.get(alter.method)
        
