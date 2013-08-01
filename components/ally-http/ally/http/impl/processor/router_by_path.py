'''
Created on Jan 30, 2013

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides a processor that routes the requests based on patterns.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, definesIf
from ally.design.processor.branch import Routing
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranching
import logging
import re

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    Context for request. 
    '''
    # ---------------------------------------------------------------- Defined
    rootURI = definesIf(str, doc='''
    @rtype: string
    The root URI of the request.
    ''')
    # ---------------------------------------------------------------- Required
    uri = requires(str)

# --------------------------------------------------------------------

@injected
class RoutingByPathHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the routing of requests based on regex patterns. The regex needs to provide
    capturing groups that joined will become the routed uri. 
    '''
    
    assembly = Assembly
    # The assembly to be used in processing the request for the provided pattern.
    rootURI = str
    # The root URI that needs to be present in order for the router to delegate to the assembly.
    
    def __init__(self):
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        assert isinstance(self.rootURI, str), 'Invalid root URI %s' % self.rootURI
        super().__init__(Routing(self.assembly))
        
        self._regex = re.compile('^%s(?:/|(?=\\.)|$)(.*)' % re.escape(self.rootURI))
            
    def process(self, chain, processing, request:Request, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Process the routing.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(request, Request), 'Invalid request %s' % request
        
        match = self._regex.match(request.uri)
        if match:
            request.uri = ''.join(match.groups())
            if Request.rootURI in request: request.rootURI = self.rootURI
            chain.route(processing)
