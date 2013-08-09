'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the access method alteration.
'''

from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.method import Method

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    access = requires(dict)

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
    # ---------------------------------------------------------------- Defined
    allowed = defines(dict, doc='''
    @rtype: dictionary{string: dictionary{string: Context}}
    The allowed access groups as a key and as value the filter contexts required for the allowed group access.
    ''')
        
class Alter(Context):
    '''
    The alter method context.
    '''
    # ---------------------------------------------------------------- Required
    target = requires(type)
    access = requires(str)
    group = requires(str)
    method = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='alterMethod')
class AlterMethod(HandlerProcessor):
    '''
    Implementation for a processor that provides the access methods alteration.
    '''
    
    def __init__(self):
        super().__init__(Access=Access, Permission=Permission)

    def process(self, chain, register:Register, add:Alter=None, remove:Alter=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Alter the access methods.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(register, Register), 'Invalid register %s' % register
        
        if add:
            assert isinstance(add, Alter), 'Invalid add method %s' % add
            if add.target != Method: return
            
            permission = self.permissionFor(register, add)
            if not permission: return chain.cancel()
            assert isinstance(permission, Permission), 'Invalid permission %s' % permission
            assert isinstance(add.group, str), 'Invalid add group %s' % add.group
            
            if permission.allowed is None: permission.allowed = {}
            if add.group not in permission.allowed: permission.allowed[add.group] = {}
            
        if remove:
            assert isinstance(remove, Alter), 'Invalid remove method %s' % remove
            if remove.target != Method: return
            
            permission = self.permissionFor(register, remove)
            if not permission: return chain.cancel()
            assert isinstance(permission, Permission), 'Invalid permission %s' % permission
            assert isinstance(remove.group, str), 'Invalid remove group %s' % remove.group
            
            if not permission.allowed or remove.group not in permission.allowed: return chain.cancel()
            permission.allowed.pop(remove.group)

    # ----------------------------------------------------------------
    
    def permissionFor(self, register, alter):
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
        return access.permissions.get(alter.method)
        
