'''
Created on Aug 13, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that provides the root URI.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    rootURI = defines(list, doc='''
    @rtype: list[string]
    The root URI path items to use for generated paths.
    ''')
    
# --------------------------------------------------------------------

@injected
class RootURIHandler(HandlerProcessor):
    '''
    Provides the root URI items to be used for generated paths.
    '''
    
    rootURI = str
    # The root URI to use for generated paths.
    
    def __init__(self):
        assert isinstance(self.rootURI, str), 'Invalid root URI %s' % self.rootURI
        super().__init__()
        
        self._itemsRoot = self.rootURI.strip('/').split('/')
    
    def process(self, chain, reply:Reply, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Populate the roor URI.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        if reply.rootURI is None: reply.rootURI = []
        reply.rootURI.extend(self._itemsRoot)
