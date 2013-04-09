'''
Created on Apr 5, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblage routing.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.branch import Routing
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranching
import re

# --------------------------------------------------------------------

class Request(Context):
    '''
    Context for request. 
    '''
    # ---------------------------------------------------------------- Required
    uri = requires(str)
    
# --------------------------------------------------------------------

@injected
class RoutingAssemblageHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the assemblage routing.
    '''
    
    assembly = Assembly
    # The assembly to be used in processing the request.
    pattern = str
    # The string pattern for matching the paths to process assemblage for, the pattern needs to provide capturing groups that 
    # joined will become the routed uri.
    
    def __init__(self):
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        assert isinstance(self.pattern, str), 'Invalid pattern %s' % self.pattern
        super().__init__(Routing(self.assembly).using('assemblage', 'Content'))
        
        self._regex = re.compile(self.pattern)

    def process(self, chain, processing, request:Request, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Provide the assemblage routing.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        
        match = self._regex.match(request.uri)
        if match:
            request.uri = ''.join(match.groups())
            chain.update(assemblage=processing.ctx.assemblage(), Content=processing.ctx.Content)
            chain.branch(processing)
        else:
            chain.proceed()
