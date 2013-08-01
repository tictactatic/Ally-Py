'''
Created on May 31, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the mandatory slash for path.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    nodes = requires(list)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Defined
    hasMandatorySlash = defines(bool, doc='''
    @rtype: boolean
    Flag indicating that a trailing slash is mandatory for path.
    ''')
    # ---------------------------------------------------------------- Required
    child = requires(Context)
    type = requires(Type)
    
# --------------------------------------------------------------------

@injected
class PathSlashHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the mandatory slash for path.
    '''
    
    def __init__(self):
        super().__init__(Node=Node)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the mandatory slash for path.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.nodes: return  # No nodes to process
        
        for node in register.nodes:
            assert isinstance(node, Node), 'Invalid node %s' % node
            if node.type and (node.type.isOf(str) or node.type.isOf(float)):
                assert isinstance(node.type, Type), 'Invalid node type %s' % node.type
                assert isinstance(node.child, Node), 'Invalid node %s' % node.child
                node.child.hasMandatorySlash = True
