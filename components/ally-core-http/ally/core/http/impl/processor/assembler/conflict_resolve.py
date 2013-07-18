'''
Created on Jun 6, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the node invokers conflicts resolving or error reporting.
'''

from ally.container.ioc import injected
from ally.core.impl.processor.assembler.base import excludeFrom, InvokerExcluded
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
    # ---------------------------------------------------------------- Required
    exclude = requires(set)
    nodes = requires(list)
    hintsCall = requires(dict)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Defined
    invokers = defines(dict)
    # ---------------------------------------------------------------- Required
    conflicts = requires(dict)
    
# --------------------------------------------------------------------

@injected
class ConflictResolveHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the node invokers conflicts resolving or error reporting.
    '''
    
    def __init__(self):
        super().__init__(Node=Node, Invoker=InvokerExcluded)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the conflict resolving.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        
        if not register.nodes: return
        
        present, reported = False, set() 
        for node in register.nodes:
            assert isinstance(node, Node), 'Invalid node %s' % node
            if not node.conflicts: continue
            assert isinstance(node.conflicts, dict), 'Invalid conflicts %s' % node.conflicts
            
            for methodHTTP, invokers in node.conflicts.items():
                if not invokers: continue
                assert isinstance(invokers, list), 'Invalid invokers %s' % invokers
                if len(invokers) > 1:
                    locations = []
                    for invoker in invokers:
                        assert isinstance(invoker, InvokerExcluded), 'Invalid invoker %s' % invoker
                        locations.append(invoker.location)
                    excludeFrom(chain, invokers)
                    
                    if reported.isdisjoint(locations):
                        log.error('Cannot use invokers because they have the same web address, at:%s', ''.join(locations))
                        reported.update(locations)
                    present = True
                else:
                    if node.invokers is None: node.invokers = {}
                    node.invokers[methodHTTP] = invokers[0]
                    
        if present and register.hintsCall:
            available = []
            for hname in sorted(register.hintsCall):
                available.append('\t%s: %s' % (hname, register.hintsCall[hname]))
            log.error('In order to make the invokers available please use one of the call hints:\n%s', '\n'.join(available))
