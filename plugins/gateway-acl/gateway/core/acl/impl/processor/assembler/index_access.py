'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Indexes the access invokers.
'''

from ally.api.operator.type import TypeProperty
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines, attribute
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
    accesses = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The access indexed by the access name.
    ''')
    accessMethods = defines(set, doc='''
    @rtype: set(string)
    All the access methods that are available.
    ''')
    # ---------------------------------------------------------------- Required
    root = requires(Context)

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    access = attribute(Context, doc='''
    @rtype: Context
    The access for the invoker.
    ''')
    # ---------------------------------------------------------------- Required
    path = requires(list)
    isFilter = requires(bool)
    shadowOf = requires(Context)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Context)
    property = requires(TypeProperty)
    
class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(dict)
    child = requires(Context)
    childByName = requires(dict)
    
class ACLAccessNode(Context):
    '''
    The ACL access context.
    '''
    # ---------------------------------------------------------------- Defined
    pattern = defines(str, doc='''
    @rtype: string
    The access pattern.
    ''')
    path = defines(list, doc='''
    @rtype: list[string|Context]
    The access path list composed of string elements and nodes for user input.
    ''')
    methods = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The access methods indexed by method name.
    ''')
    
class ACLMethodInvoker(Context):
    '''
    The ACL method context.
    '''
    # ---------------------------------------------------------------- Defined
    invoker = attribute(Context, doc='''
    @rtype: Context
    The method invoker.
    ''')
    nodesProperties = defines(dict, doc='''
    @rtype: dictionary{Context: TypeProperty}
    The property types indexed by node contexts that are found in the access path.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='indexAccess')
class IndexAccessHandler(HandlerProcessor):
    '''
    Implementation for a processor that indexes the access invokers by name.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker, Element=Element, Node=Node)

    def process(self, chain, register:Register, ACLAccess:ACLAccessNode, ACLMethod:ACLMethodInvoker, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Indexes the access invokers by name.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(ACLAccess, ACLAccessNode), 'Invalid access class %s' % ACLAccess
        assert issubclass(ACLMethod, ACLMethodInvoker), 'Invalid method class %s' % ACLMethod
        if not register.root: return  # No root to process
        
        stack, methods, accessShadows = deque(), [], {}
        stack.append(([], register.root))
        while stack:
            path, node = stack.popleft()
            assert isinstance(node, Node), 'Invalid node %s' % node
            if node.invokers:
                assert isinstance(node.invokers, dict), 'Invalid invokers %s' % node.invokers
                if register.accesses is None: register.accesses = {}
                if register.accessMethods is None: register.accessMethods = set()
                
                nmethods, shadows = {}, []
                for method, invoker in node.invokers.items():
                    assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
                    if invoker.isFilter: continue
                    
                    if invoker.shadowOf:
                        shadows.append((method, invoker))
                        continue
                    assert invoker.access is None, 'Invoker %s already has access %s' % invoker.access
                    
                    nmethods[method] = ACLMethod(invoker=invoker)
                    register.accessMethods.add(method)
                    
                if nmethods or shadows:
                    pattern = '/'.join(el if isinstance(el, str) else '*' for el in path)
                    name = '{0:0>8x}'.format(binascii.crc32(pattern.encode(), 0)).upper()
                    
                    access = register.accesses.get(name)
                    if access is None: access = register.accesses[name] = ACLAccess(pattern=pattern, path=path)
                    else:
                        assert isinstance(access, ACLAccessNode), 'Invalid access %s' % access
                        assert pattern == access.pattern, \
                        'Invalid pattern \'%s\' with pattern \'%s\' for name \'%s\'' % (pattern, access.pattern, name)
                        assert path == access.path, \
                        'Invalid path \'%s\' with path \'%s\' for \'%s\'' % (path, access.path, pattern)
                        
                    if access.methods is None: access.methods = {}
                    if shadows: accessShadows[access] = shadows
                    for method, aclMethod in nmethods.items():
                        assert isinstance(aclMethod, ACLMethodInvoker), 'Invalid ACL method %s' % aclMethod
                        assert isinstance(aclMethod.invoker, Invoker), 'Invalid invoker %s' % aclMethod.invoker
                        assert method not in access.methods, 'Already a method for \'%s\' at %s' % (method, pattern)
                        assert aclMethod.invoker.access is None, 'Invoker %s already has access %s' % aclMethod.invoker.access
                        aclMethod.invoker.access = access
                        access.methods[method] = aclMethod
                        methods.append(aclMethod)
            
            if node.childByName:
                for cname, cnode in node.childByName.items():
                    cpath = list(path)
                    cpath.append(cname)
                    stack.append((cpath, cnode))
            if node.child:
                cpath = list(path)
                cpath.append(node)
                stack.append((cpath, node.child))
                
        for access, shadows in accessShadows.items():
            assert isinstance(access, ACLAccessNode), 'Invalid access %s' % access
            for method, shadow in shadows:
                assert isinstance(shadow, Invoker), 'Invalid invoker %s' % shadow
                assert isinstance(shadow.shadowOf, Invoker), 'Invalid invoker %s' % shadow.shadowOf
                assert isinstance(shadow.shadowOf.access, ACLAccessNode), 'Invalid access %s' % shadow.shadowOf.access
                assert method not in access.methods, 'Already a method for \'%s\' at %s' % (method, access.pattern)
                
                access.methods[method] = shadow.shadowOf.access.methods[method]
            
        for method in methods:
            assert isinstance(method, ACLMethodInvoker), 'Invalid method %s' % method
            assert isinstance(method.invoker, Invoker), 'Invalid invoker %s' % method.invoker
            
            if method.nodesProperties is None: method.nodesProperties = {}
            for el in method.invoker.path:
                assert isinstance(el, Element), 'Invalid element %s' % el
                if not el.property: continue
                assert isinstance(el.node, Node), 'Invalid element node %s' % el.node
                method.nodesProperties[el.node] = el.property
