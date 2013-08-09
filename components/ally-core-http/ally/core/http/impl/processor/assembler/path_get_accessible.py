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
from ally.api.operator.type import TypeModel, TypeProperty
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
    isModel = requires(bool)
    path = requires(list)
    
class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    property = requires(TypeProperty)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(dict)
    invokersGet = requires(dict)
    child = requires(Context)
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
        super().__init__(Invoker=Invoker, Element=Element, Node=Node)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the accessible invokers.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.nodes: return  # No nodes to process
        
        for current in register.nodes:
            assert isinstance(current, Node), 'Invalid node %s' % current
        
            for name, node in self.iterAvailable(current):
                if node.invokers and HTTP_GET in node.invokers:
                    if current.invokersAccessible is None: current.invokersAccessible = []
                    current.invokersAccessible.append((name, node.invokers[HTTP_GET]))
           
    # ----------------------------------------------------------------
    
    def iterAvailable(self, node):
        '''
        Iterates all the available nodes for node.
        '''
        assert isinstance(node, Node), 'Invalid node %s' % node
        target = None
        if node.invokers and HTTP_GET in node.invokers:
            invoker = node.invokers[HTTP_GET]
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.isModel and invoker.target: target = invoker.target
            
        if target:
            for cname, cnode in self.iterTarget('', node, target): yield cname, cnode
        
        for cname, cnode in self.iterChildByName('', node):
            yield cname, cnode
            if target:
                for cname, cnode in self.iterTarget(cname, cnode, target): yield cname, cnode
        
        if target and node.invokersGet:
            for parent in inheritedTypesFrom(target.clazz, TypeModel):
                assert isinstance(parent, TypeModel), 'Invalid parent %s' % parent
                if not parent.propertyId: continue
                propInvoker = node.invokersGet.get(parent.propertyId)
                if propInvoker and propInvoker.node:
                    assert isinstance(propInvoker, Invoker), 'Invalid invoker %s' % propInvoker
                    for cname, cnode in self.iterTarget('', propInvoker.node, parent): yield cname, cnode
    
    def iterTarget(self, name, node, target):
        '''
        Iterates all the nodes that are made available by properties in the target.
        '''
        assert isinstance(target, TypeModel), 'Invalid target model %s' % target
        assert isinstance(node, Node), 'Invalid node %s' % node
        if not node.child: return
        assert isinstance(node.child, Node), 'Invalid node %s' % node.child
        for cname, cnode in self.iterChildByName(name, node.child):
            assert isinstance(cnode, Node), 'Invalid node %s' % cnode
            if not cnode.invokers or not HTTP_GET in cnode.invokers: continue
            invoker = cnode.invokers[HTTP_GET]
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            for el in reversed(invoker.path):
                assert isinstance(el, Element), 'Invalid element %s' % el
                if el.property:
                    assert isinstance(el.property, TypeProperty), 'Invalid property %s' % el.property
                    if el.property.parent == target and el.property.name in target.properties:
                        yield cname, cnode
                        for cname, cnode in self.iterChildByName(cname, cnode): yield cname, cnode
                    break
    
    def iterChildByName(self, name, node):
        '''
        Iterates all the nodes that are directly available under the child by name attribute in the node.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        stack = deque()
        stack.append((name, node))
        while stack:
            name, node = stack.popleft()
            assert isinstance(node, Node), 'Invalid node %s' % node
            if not node.childByName: continue
            for cname, cnode in node.childByName.items():
                cname = ''.join((name, cname))
                yield cname, cnode
                stack.append((cname, cnode))
            
