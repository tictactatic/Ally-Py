'''
Created on May 31, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Finds all get invokers that can be directly accessed without the need of extra information, basically all paths that can be
directly related to a node.
'''

from ally.api.operator.extract import inheritedTypesFrom
from ally.api.operator.type import TypeModel
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.server import HTTP_GET
from collections import deque

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    nodes = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Context)
    target = requires(TypeModel)
    isCollection = requires(bool)
    isModel = requires(bool)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(dict)
    invokersGet = requires(dict)
    childByName = requires(dict)
    # ---------------------------------------------------------------- Defined
    invokersAccessible = defines(list, doc='''
    @rtype: list[tuple(string, Context)]
    The list of invokers tuples that are accessible for this node, the first entry in tuple is a generated invoker name.
    ''')
    
# --------------------------------------------------------------------

class PathGetAccesibleHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the accessible invokers for a node.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker, Node=Node)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the accessible invokers.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.nodes: return  # No nodes to process
        
        # We find first the direct accessible paths
        stack = deque()
        for current in register.nodes:
            assert isinstance(current, Node), 'Invalid node %s' % current
            
            self.pushAvailable('', current, stack)
            if not stack: continue
            
            if current.invokersAccessible is None: current.invokersAccessible = []
            while stack:
                name, node = stack.popleft()
                assert isinstance(node, Node)
                if node.invokers and HTTP_GET in node.invokers:
                    current.invokersAccessible.append((name, node.invokers[HTTP_GET]))
                
                self.pushAvailable(name, node, stack)

    # ----------------------------------------------------------------
    
    def pushAvailable(self, name, node, stack):
        '''
        Pushes the available nodes to the provided stack.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(node, Node), 'Invalid node %s' % node
        assert isinstance(stack, deque), 'Invalid stack %s' % stack
        
        if node.childByName: stack.extend((''.join((name, cname)), cnode) for cname, cnode in node.childByName.items())
        
        if not node.invokers or not node.invokersGet: return
        
        invoker = node.invokers.get(HTTP_GET)
        if not invoker: return
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
    
        if not invoker.isCollection and invoker.isModel and invoker.target:
            assert isinstance(invoker.target, TypeModel), 'Invalid target %s' % invoker.target
            
            self.pushAvailableForProperties(name, node, invoker.target, stack)
                
            for parent in inheritedTypesFrom(invoker.target.clazz, TypeModel):
                assert isinstance(parent, TypeModel), 'Invalid parent %s' % parent
                if not parent.propertyId: continue
                nodeParent = node.invokersGet.get(parent.propertyId)
                if nodeParent: self.pushAvailableForProperties(name, nodeParent, parent, stack)
    
    def pushAvailableForProperties(self, name, node, model, stack):
        '''
        Pushes the available nodes based on paths found by properties.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(node, Node), 'Invalid node %s' % node
        assert isinstance(model, TypeModel), 'Invalid model %s' % model
        assert isinstance(stack, deque), 'Invalid stack %s' % stack
        
        for prop in model.properties.values():
            invokerByProp = node.invokersGet.get(prop)
            if not invokerByProp: continue
            assert isinstance(invokerByProp, Invoker), 'Invalid invoker %s' % invokerByProp
            if not invokerByProp.node or invokerByProp.node == node: continue
            assert isinstance(invokerByProp.node, Node), 'Invalid node %s' % invokerByProp.node
            if not invokerByProp.node.childByName: continue
            stack.extend((''.join((name, cname)), cnode) for cname, cnode in invokerByProp.node.childByName.items())
            
