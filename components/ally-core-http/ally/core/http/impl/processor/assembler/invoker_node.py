'''
Created on May 29, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the node based on invokers.
'''

from ally.api.operator.type import TypeProperty
from ally.api.type import Type
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Abort
from ally.design.processor.handler import HandlerProcessor
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Defined
    root = defines(Context, doc='''
    @rtype: Context
    The root node.
    ''')
    nodes = defines(list, doc='''
    @rtype: list[Context]
    The list of nodes that are found in root.
    ''')
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    node = defines(Context, doc='''
    @rtype: Context
    The invoker node.
    ''')
    # ---------------------------------------------------------------- Optional
    shadowing = optional(Context)
    # ---------------------------------------------------------------- Required
    methodHTTP = requires(str)
    path = requires(list)
    location = requires(str)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Defined
    node = defines(Context, doc='''
    @rtype: Context
    The element node.
    ''')
    # ---------------------------------------------------------------- Required
    name = requires(str)
    property = requires(TypeProperty)
    
class NodeInvoker(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Defined
    parent = defines(Context, doc='''
    @rtype: Context
    The parent node.
    ''')
    invokers = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The invokers indexed by the HTTP method name.
    ''')
    conflicts = defines(dict, doc='''
    @rtype: dictionary{string: list[Context]}
    The invokers indexed by the HTTP method name that conflict with the invoker associated with the method in 'invokers'.
    ''')
    child = defines(Context, doc='''
    @rtype: Context
    The direct child node for a user input value.
    ''')
    childByName = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The child nodes indexed by name.
    ''')
    type = defines(Type, doc='''
    @rtype: Type
    The type represented by the child node.
    ''')
    
# --------------------------------------------------------------------

@injected
class InvokerNodeHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the node based on invokers.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker, Element=Element)

    def process(self, chain, register:Register, Node:NodeInvoker, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the path based on elements.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(register.exclude, set), 'Invalid exclude set %s' % register.exclude
        assert issubclass(Node, NodeInvoker), 'Invalid node class %s' % Node
        
        if not register.invokers: return  # No invokers to process
        
        if register.nodes is None: register.nodes = []
        if register.root is None:
            register.root = Node()
            register.nodes.append(register.root)
        
        aborted, checkReported = [], self.createReported()
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            assert isinstance(invoker.methodHTTP, str), 'Invalid HTTP method name %s' % invoker.methodHTTP
            node = register.root
            assert isinstance(node, NodeInvoker), 'Invalid node %s' % node
            
            valid = True
            if invoker.path:
                for el in invoker.path:
                    assert isinstance(el, Element), 'Invalid element %s' % el
                    if el.property:
                        assert isinstance(el.property, TypeProperty)
                        
                        if not el.property.type.isPrimitive:
                            if checkReported(invoker):
                                log.error('Cannot use because the %s is not a primitive, at:%s', el.property, invoker.location)
                            valid = False
                            break
                        
                        if node.type is None: node.type = el.property.type
                        elif node.type != el.property.type:
                            if checkReported(invoker):
                                log.error('Cannot use because the property %s is expected to be %s, at:%s',
                                          el.property, node.type, invoker.location)
                            valid = False
                            break
                        
                        assert isinstance(node.type, Type), 'Invalid node type %s' % node.type
                        if node.type.isOf(str) and node.childByName:
                            if checkReported(invoker):
                                log.error('Cannot use because the node already has named children (%s) and cannot use with '
                                          'string property \'%s\', at:%s', ', '.join(str(childName) 
                                                            for childName in node.childByName), el.property, invoker.location)
                            valid = False
                            break
                        
                        el.node = node
                        if node.child is None:
                            node.child = Node(parent=node)
                            register.nodes.append(node.child)
                        node = node.child
                    else:
                        assert isinstance(el.name, str) and el.name, 'Invalid element name %s' % el.name
                            
                        if node.type and node.type.isOf(str):
                            if checkReported(invoker):
                                log.error('Cannot use because the node represents a string property and cannot add name '
                                          '\'%s\', at:%s', el.name, invoker.location)
                            valid = False
                            break
                        
                        el.node = node
                        if node.childByName is None: node.childByName = {}
                        cnode = node.childByName.get(el.name)
                        if cnode is None:
                            cnode = node.childByName[el.name] = Node(parent=node)
                            register.nodes.append(cnode)
                        node = cnode
            
            if not valid: aborted.append(invoker)
            else:
                if node.invokers is None: node.invokers = {invoker.methodHTTP: invoker}
                elif node.conflicts and invoker.methodHTTP in node.conflicts:
                    node.conflicts[invoker.methodHTTP].append(invoker)
                    continue
                elif invoker.methodHTTP in node.invokers:
                    if node.conflicts is None: node.conflicts = {}
                    conflicts = node.conflicts.get(invoker.methodHTTP)
                    if conflicts is None: 
                        conflicts = node.conflicts[invoker.methodHTTP] = [node.invokers.pop(invoker.methodHTTP)]
                    conflicts.append(invoker)
                    continue
                else: node.invokers[invoker.methodHTTP] = invoker
                invoker.node = node
                
        if aborted: raise Abort(*aborted)

    # ----------------------------------------------------------------
    
    def createReported(self):
        '''
        Helper to check the reported status for invokers.
        '''
        reported = set()
        def check(invoker):
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.location in reported: return False
            if Invoker.shadowing in invoker and invoker.shadowing: return False
            reported.add(invoker)
            return True
        return check
