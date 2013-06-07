'''
Created on May 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the slice option values handling.
'''

from ally.api.option import Slice, SliceAndTotal
from ally.api.type import Input, typeFor
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from collections import Callable
from functools import partial

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
    # ---------------------------------------------------------------- Defined
    prepare = defines(Callable)
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)
    location = requires(str)

# --------------------------------------------------------------------

class OptionSliceHandler(HandlerProcessor):
    '''
    Implementation for a processor that enforces collection slicing values.
    '''
    
    maximumLimit = None
    # The maximum allowed limit.
    defaultLimit = None
    # The default limit.
    defaultWithTotal = None
    # The default value for providing the total count.

    def __init__(self):
        '''
        Construct the handler.
        '''
        assert self.maximumLimit is None or isinstance(self.maximumLimit, int), 'Invalid maximum limit %s' % self.maximumLimit
        assert self.defaultLimit is None or isinstance(self.defaultLimit, int), 'Invalid default limit %s' % self.defaultLimit
        assert self.defaultWithTotal is None or isinstance(self.defaultWithTotal, bool), \
        'Invalid default with total %s' % self.defaultWithTotal
        super().__init__(Invoker=Invoker)
        
        self.typeLimit = typeFor(Slice.limit)
        self.typeTotal = typeFor(SliceAndTotal.withTotal)
        
    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the slicing options values.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return  # No invokers to process
        
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if not invoker.inputs: continue
            
            hasLimit = hasTotal = False
            for inp in invoker.inputs:
                assert isinstance(inp, Input), 'Invalid input %s' % inp
                if inp.type == self.typeLimit: hasLimit = True
                elif inp.type == self.typeTotal: hasTotal = True
            # TODO: Gabriel: add notifications of possible option usage
            if hasLimit or hasTotal: invoker.prepare = partial(self.prepare, hasLimit, hasTotal, invoker.prepare)
    
    # ----------------------------------------------------------------
    
    def prepare(self, hasLimit, hasTotal, wrapped, arguments):
        '''
        Prepares the arguments for invoking.
        '''
        assert isinstance(arguments, dict), 'Invalid arguments %s' % arguments
        
        if hasLimit:
            limit = arguments.get(self.typeLimit)
            if limit is None:
                if self.defaultLimit is not None: arguments[self.typeLimit] = self.defaultLimit
                elif self.maximumLimit is not None: arguments[self.typeLimit] = self.maximumLimit
            elif self.maximumLimit and limit > self.maximumLimit: arguments[self.typeLimit] = self.maximumLimit
            
        if hasTotal:
            if arguments.get(self.typeTotal) is None: arguments[self.typeTotal] = self.defaultWithTotal
