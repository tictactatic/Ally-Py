'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the method names and objects.
'''

from . import get_access
from ally.container.support import setup
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.method import Method
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
    
class Get(get_access.Get):
    '''
    The get method context.
    '''
    # ---------------------------------------------------------------- Required
    forAccess = requires(str)
    forGroup = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='getMethod')
class GetMethod(HandlerProcessor):
    '''
    Implementation for a processor that provides the methods names and objects.
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
        if not register.accessMethods or not register.access: return
        assert isinstance(register.accessMethods, set), 'Invalid methods access %s' % register.accessMethods
        assert isinstance(register.access, dict), 'Invalid access %s' % register.access
        if not get: return
        assert isinstance(get, Get), 'Invalid get method %s' % get
        if get.target not in (Method, Method.Name): return
        
        if get.forName is not None:
            if get.forName not in register.accessMethods: return chain.cancel()
            if get.target == Method: get.value = self.create(get.forName)
            else: get.value = get.forName
        
        elif get.forAccess is not None:
            access = register.access.get(get.forAccess)
            if not access: return chain.cancel()
            assert isinstance(access, Access), 'Invalid access %s' % access
            if not access.permissions: return
            assert isinstance(access.permissions, dict), 'Invalid access permissions %s' % access.permissions
            if get.forGroup:
                names = []
                for method, permission in access.permissions.items():
                    assert isinstance(permission, Permission), 'Invalid permission %s' % permission
                    if not permission.allowed: continue
                    if get.forGroup in permission.allowed: names.append(method)
            else:
                names = access.permissions.keys()
            
            if get.target == Method: values = (self.create(name) for name in names)
            else: values = names
            if get.value is not None: get.value = itertools.chain(get.names, values)
            else: get.value = values
            
        elif get.forAll:
            if get.target == Method: values = (self.create(name) for name in register.accessMethods)
            else: values = register.accessMethods
            if get.value is not None: get.value = itertools.chain(get.value, values)
            else: get.value = values

    # ----------------------------------------------------------------
    
    def create(self, name):
        '''
        Create the method.
        '''
        value = Method()
        value.Name = name
        
        return value
