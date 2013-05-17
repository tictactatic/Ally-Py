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
from ally.core.spec.codes import Coded
from ally.core.spec.resources import Invoker
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Invoker)
    arguments = requires(dict)

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
        super().__init__()
        
    def process(self, chain, request:Request, response:Coded, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the slicing options values.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Coded), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error
        
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        assert isinstance(request.arguments, dict), 'Invalid arguments %s' % request.arguments
        
        for inp in request.invoker.inputs:
            assert isinstance(inp, Input), 'Invalid input %s' % inp
            if inp.type == typeFor(Slice.limit):
                limit = request.arguments.get(inp.name)
                if limit is None:
                    if self.defaultLimit is not None: request.arguments[inp.name] = self.defaultLimit
                    elif self.maximumLimit is not None: request.arguments[inp.name] = self.maximumLimit
                elif self.maximumLimit and limit > self.maximumLimit: request.arguments[inp.name] = self.maximumLimit
            elif inp.type == typeFor(SliceAndTotal.withTotal):
                if request.arguments.get(inp.name) is None: request.arguments[inp.name] = self.defaultWithTotal
