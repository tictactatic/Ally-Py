'''
Created on Jun 5, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the validation for solved inputs.
'''

from ally.api.type import Input
from ally.design.processor.attribute import requires
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
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)
    solved = requires(set)
    location = requires(str)
    
# --------------------------------------------------------------------

class ValidateSolvedHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the validation for solved inputs.
    '''
    
    def __init__(self):
        super().__init__(Invoker=Invoker)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the solved inputs.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return  # No invokers to process.
        
        reported, aborted = set(), []
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if not invoker.inputs: continue
            
            if invoker.solved is None: solved = frozenset()
            else: solved = invoker.solved
            
            unsolved, keep = [], True
            for inp in invoker.inputs:
                assert isinstance(inp, Input), 'Invalid input %s' % inp
                if inp not in solved:
                    unsolved.append('\'%s\'' % inp.name)
                    if not inp.hasDefault: keep = False
            
            if not keep:
                if invoker.location not in reported:
                    log.error('Cannot use because of unsolved inputs %s, at:%s', ', '.join(unsolved), invoker.location)
                    reported.add(invoker.location)
                aborted.append(invoker)
        
        if aborted: raise Abort(*aborted)
