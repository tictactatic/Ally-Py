'''
Created on May 29, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the node based on invokers.
'''

from ally.api.operator.type import TypeProperty
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
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
    # ---------------------------------------------------------------- Required
    methodHTTP = requires(str)
    path = requires(list)
    location = requires(str)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    property = requires(TypeProperty)
    
class NodeInvoker(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Defined
    byName = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The child nodes indexed by name.
    ''')
    byType = defines(dict, doc='''
    @rtype: dictionary{Type: Context}
    The child nodes indexed by type.
    ''')
    properties = defines(set, doc='''
    @rtype: set(TypeProperty)
    The properties types that will are associated with the node value.
    ''')
    invokers = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The invokers indexed by the HTTP method name.
    ''')
    conflicts = defines(dict, doc='''
    @rtype: dictionary{string: list[Context]}
    The invokers indexed by the HTTP method name that conflict with the invoker associated with the method in 'invokers'.
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
        assert issubclass(Node, NodeInvoker), 'Invalid node class %s' % Node
        
        if not register.invokers: return  # No invokers to process
        assert isinstance(register.invokers, list), 'Invalid invokers %s' % register.invokers
        
        if register.nodes is None: register.nodes = []
        if register.root is None:
            register.root = Node()
            register.nodes.append(register.root)
        k = 0
        while k < len(register.invokers):
            invoker = register.invokers[k]
            k += 1
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
                            
                        if node.byName:
                            log.error('Cannot use because the node already has names (%s) and cannot add type \'%s\', at:%s',
                                     ', '.join(str(typ) for typ in node.byName), el.property.type, invoker.location)
                            k -= 1
                            del register.invokers[k]
                            valid = False
                            break
                        
                        if not el.property.type.isPrimitive:
                            log.error('Cannot use because the %s is not a primitive, at:%s', el.property, invoker.location)
                            k -= 1
                            del register.invokers[k]
                            valid = False
                            break
                        
                        if node.byType is None: node.byType = {}
                        cnode = node.byType.get(el.property.type)
                        if cnode is None:
                            cnode = node.byType[el.property.type] = Node()
                            register.nodes.append(cnode)
                        if cnode.properties is None: cnode.properties = set()
                        cnode.properties.add(el.property)
                    else:
                        assert isinstance(el.name, str) and el.name, 'Invalid element name %s' % el.name
                            
                        if node.byType:
                            log.error('Cannot use because the node already has types (%s) and cannot add name \'%s\', at:%s',
                                     ', '.join(str(typ) for typ in node.byType), el.name, invoker.location)
                            k -= 1
                            del register.invokers[k]
                            valid = False
                            break
                        
                        if node.byName is None: node.byName = {}
                        cnode = node.byName.get(el.name)
                        if cnode is None:
                            cnode = node.byName[el.name] = Node()
                            register.nodes.append(cnode)
                        
                    node = cnode
            
            if not valid: continue
            
            if node.invokers is None: node.invokers = {invoker.methodHTTP: invoker}
            elif node.conflicts and invoker.methodHTTP in node.conflicts: node.conflicts[invoker.methodHTTP].append(invoker)
            elif invoker.methodHTTP in node.invokers:
                if node.conflicts is None: node.conflicts = {}
                conflicts = node.conflicts.get(invoker.methodHTTP)
                if conflicts is None: conflicts = node.conflicts[invoker.methodHTTP] = [node.invokers.pop(invoker.methodHTTP)]
                conflicts.append(invoker)
                continue
            else: node.invokers[invoker.methodHTTP] = invoker
            invoker.node = node
