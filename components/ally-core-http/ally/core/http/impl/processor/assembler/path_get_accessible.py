'''
Created on May 31, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Finds all get invokers that can be directly accessed without the need of extra information, basically all paths that can be
directly related to a node.
'''

from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.server import HTTP_GET
from collections import deque, OrderedDict
from ally.support.util import firstOf

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
    path = requires(list)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    byName = requires(dict)
    byType = requires(dict)
    invokers = requires(dict)
    # ---------------------------------------------------------------- Defined
    invokersAccessible = defines(OrderedDict, doc='''
    @rtype: dictionary{string: Context}
    The dictionary of invokers that are accessible for this node indexed by a unique generated invoker name.
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
            if not current.byName: continue
            
            accessible = []
            stack.extend(current.byName.items())
            while stack:
                name, node = stack.popleft()
                if node.invokers and HTTP_GET in node.invokers:
                    accessible.append((name, node.invokers[HTTP_GET]))
                if node.byName: stack.extend((''.join((name, cname)), cnode) for cname, cnode in node.byName.items())
            accessible.sort(key=firstOf)
            if current.invokersAccessible is None: current.invokersAccessible = OrderedDict()
            current.invokersAccessible.update(accessible)
        # TODO: Gabriel: add also the invokers that have compatible input types
