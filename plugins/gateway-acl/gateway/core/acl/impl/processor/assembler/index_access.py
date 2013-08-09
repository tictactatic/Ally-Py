'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Indexes the access invokers.
'''

from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from collections import deque
import binascii

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    access = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The access indexed by the access name.
    ''')
    accessMethods = defines(set, doc='''
    @rtype: set(string)
    All the access methods that are available.
    ''')
    # ---------------------------------------------------------------- Required
    root = requires(Context)

class Node(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(dict)
    child = requires(Context)
    childByName = requires(dict)
    
class AccessNode(Context):
    '''
    The access context.
    '''
    # ---------------------------------------------------------------- Defined
    pattern = defines(str, doc='''
    @rtype: string
    The access pattern.
    ''')
    path = defines(tuple, doc='''
    @rtype: tuple(string|Context)
    The access tuple composed of string elements and nodes for user input.
    ''')
    permissions = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The access permissions indexed by method.
    ''')
    
class PermissionInvoker(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Defined
    invoker = defines(Context, doc='''
    @rtype: Context
    The permission invoker.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='indexAccess')
class IndexAccessHandler(HandlerProcessor):
    '''
    Implementation for a processor that indexes the access invokers by name.
    '''
    
    propertyMark = '*'
    # The mark to place instead of property elements.
    
    def __init__(self):
        assert isinstance(self.propertyMark, str), 'Invalid property mark %s' % self.propertyMark
        super().__init__(Node=Node)

    def process(self, chain, register:Register, Access:AccessNode, Permission:PermissionInvoker, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Indexes the access invokers by name.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Access, AccessNode), 'Invalid access class %s' % Access
        assert issubclass(Permission, PermissionInvoker), 'Invalid permission class %s' % Permission
        if not register.root: return  # No root to process
        
        stack = deque()
        stack.append(((), register.root))
        while stack:
            path, node = stack.popleft()
            assert isinstance(node, Node), 'Invalid node %s' % node
            if node.invokers:
                assert isinstance(node.invokers, dict), 'Invalid invokers %s' % node.invokers
                if register.access is None: register.access = {}
                if register.accessMethods is None: register.accessMethods = set()
                
                pattern = '/'.join(el if isinstance(el, str) else self.propertyMark for el in path)
                name = '{0:0>8x}'.format(binascii.crc32(pattern.encode(), 0)).upper()
                
                access = register.access.get(name)
                if access is None: access = register.access[name] = Access(pattern=pattern, path=path)
                else:
                    assert isinstance(access, AccessNode), 'Invalid access %s' % access
                    assert pattern == access.pattern, \
                    'Invalid pattern \'%s\' with pattern \'%s\' for name \'%s\'' % (pattern, access.pattern, name)
                    assert path == access.path, \
                    'Invalid path \'%s\' with path \'%s\' for name \'%s\'' % (path, access.path, name)
                    
                if access.permissions is None: access.permissions = {}
                
                for method, invoker in node.invokers.items():
                    assert method not in access.permissions, 'Already a permission for \'%s\' at %s' % (method, name)
                    access.permissions[method] = Permission(invoker=invoker)
                    register.accessMethods.add(method)
            
            if node.childByName:
                for cname, cnode in node.childByName.items(): stack.append((path + (cname,), cnode))
            if node.child:
                stack.append((path + (node,), node.child))
