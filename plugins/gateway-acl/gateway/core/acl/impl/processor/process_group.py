'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the associated group names.
'''

from .get_filter import Get
from ally.container import wire
from ally.container.support import setup
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.group import Group
import itertools

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    access = requires(dict)
    accessMethods = requires(set)

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
    
class Alter(Context):
    '''
    The alter context.
    '''
    # ---------------------------------------------------------------- Required
    group = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='processGroup')
class ProcessGroup(HandlerProcessor):
    '''
    Implementation for a processor that provides the associated group names.
    '''
    
    acl_groups = {
              'Anonymous': 'This group contains the services that can be accessed by anyone',
              }; wire.config('acl_groups', doc='''
    The allow access pattern place holders that are placed where a identifier is expected.''')
    
    def __init__(self):
        assert isinstance(self.acl_groups, dict), 'Invalid acl groups %s' % self.acl_groups
        super().__init__(Access=Access)

    def process(self, chain, register:Register, get:Get=None, add:Alter=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the associated group names.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.accessMethods or not register.access: return
        assert isinstance(register.accessMethods, set), 'Invalid methods access %s' % register.accessMethods
        assert isinstance(register.access, dict), 'Invalid access %s' % register.access
        if not get:
            if add:
                assert isinstance(add, Alter), 'Invalid add %s' % add
                if add.group and add.group not in self.acl_groups: chain.cancel()
            return
        assert isinstance(get, Get), 'Invalid get method %s' % get
        if get.forGroup and get.forGroup not in self.acl_groups: return chain.cancel()
        if get.target not in (Group, Group.Name): return
        
        if get.forName is not None:
            if get.forName not in self.acl_groups: return chain.cancel()
            if get.target == Group: get.value = self.create(get.forName)
            else: get.value = get.forName
            
        if get.forAccess is not None:
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
                names.update(permission.allowed)
            
            if get.target == Group: values = (self.create(name) for name in names)
            else: values = names
            if get.value is not None: get.value = itertools.chain(get.names, values)
            else: get.value = values
            
        elif get.forAll:
            if get.target == Group: values = (self.create(name) for name in self.acl_groups)
            else: values = self.acl_groups.keys()
            if get.value is not None: get.value = itertools.chain(get.value, values)
            else: get.value = values

    # ----------------------------------------------------------------
    
    def create(self, name):
        '''
        Create the group.
        '''
        value = Group()
        value.Name = name
        value.Description = self.acl_groups[name]
        
        return value
