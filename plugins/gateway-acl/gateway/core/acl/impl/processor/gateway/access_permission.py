'''
Created on Aug 9, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that generates gateway permissions for configured access.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import defines, requires, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from collections import Iterable
import itertools
import re

# --------------------------------------------------------------------

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    permissions = defines(Iterable, doc='''
    @rtype: Iterable(Gateway)
    The access permissions.
    ''')
    # ---------------------------------------------------------------- Optional
    rootURI = optional(list)
    # ---------------------------------------------------------------- Required
    identifiers = requires(Iterable)
    
class PermissionACL(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Defined
    method = defines(str, doc='''
    @rtype: string
    The method name for permission.
    ''')
    path = defines(str, doc='''
    @rtype: string
    The permission path.
    ''')
    pathMarkers = defines(dict, doc='''
    @rtype: dictionary{Context: string}
    A dictionary containing the path marker value indexed by the node.
    ''')
    filters = defines(dict, doc='''
    @rtype: dictionary{string: object}
    The filters for permission, as a key the filter name and as a value the filter object.
    ''')

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    accesses = requires(dict)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    
class ACLAccess(Context):
    '''
    The ACL access context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(list)
    methods = requires(dict)

class ACLMethod(Context):
    '''
    The ACL method context.
    '''
    # ---------------------------------------------------------------- Required
    allowed = requires(dict)
     
# --------------------------------------------------------------------

@injected
@setup(Handler, name='accessPermission')
class AccessPermission(HandlerProcessor):
    '''
    Provides the handler that generates gateway permissions for configured access.
    '''
    def __init__(self):
        super().__init__(Node=Node, ACLAccess=ACLAccess, ACLMethod=ACLMethod)
    
    def process(self, chain, reply:Reply, register:Register, Permission:PermissionACL, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the access permissions.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        assert isinstance(register, Register), 'Invalid register %s' % register
        if reply.identifiers is None or not register.accesses: return
        assert isinstance(register.accesses, dict), 'Invalid register accesses %s' % register.accesses
        
        if Reply.rootURI in reply: rootURI = reply.rootURI
        else: rootURI = None
        permissions = self.iterPermissions(register.accesses.values(), set(reply.identifiers), Permission, rootURI)
        if reply.permissions is not None: reply.permissions = itertools.chain(reply.permissions, permissions)
        else: reply.permissions = permissions
        
    # ----------------------------------------------------------------
    
    def iterPermissions(self, accesses, identifiers, Permission, rootURI=None):
        '''
        Iterates the permissions for the provided accesses.
        '''
        assert isinstance(accesses, Iterable), 'Invalid accesses %s' % accesses
        assert isinstance(identifiers, set), 'Invalid identifiers %s' % identifiers
        assert issubclass(Permission, PermissionACL), 'Invalid permission class %s' % Permission
        assert rootURI is None or isinstance(rootURI, list), 'Invalid root URI %s' % rootURI
        for access in accesses:
            assert isinstance(access, ACLAccess), 'Invalid access %s' % access
            if not access.methods: continue
            assert isinstance(access.methods, dict), 'Invalid methods %s' % access.methods
            
            items, k, pathMarkers = [], 1, {}
            if rootURI: items.extend(re.escape(el) for el in rootURI)
            for el in access.path:
                if isinstance(el, str): items.append(re.escape(el))
                else:
                    assert isinstance(el, Node), 'Invalid node %s' % el
                    assert isinstance(el.type, Type), 'Invalid type %s' % el.type
                    if el.type.isOf(int): items.append('([0-9\\-]+)')
                    else: items.append('([^\\/]+)')
                    pathMarkers[el] = '{%s}' % k
                    k += 1
            path = '%s[\\/]?(?:\\.|$)' % '\\/'.join(items)
            
            for name, method in access.methods.items():
                assert isinstance(method, ACLMethod), 'Invalid method %s' % method
                if not method.allowed: continue
                midentifiers = identifiers.intersection(method.allowed)
                if not midentifiers: continue
                permission = Permission()
                assert isinstance(permission, PermissionACL), 'Invalid permission %s' % permission
                permission.method = name
                permission.path = path
                permission.pathMarkers = pathMarkers
                permission.filters = {}
                for identifier in midentifiers: permission.filters.update(method.allowed[identifier])
                
                yield permission
