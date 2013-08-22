'''
Created on Aug 21, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that injects groups names.
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
    groups = defines(set, doc='''
    @rtype: set(string)
    The groups names to create gateways for.
    ''')
    
# --------------------------------------------------------------------

@injected
class GroupSpecifierHandler(HandlerProcessor):
    '''
    Provides the handler that injects groups for gateways.
    '''
    
    groups = list
    # The groups names to provide the gateways for.
    
    def __init__(self):
        assert isinstance(self.groups, list), 'Invalid ACL groups %s' % self.groups
        assert self.groups, 'At least an ACL group is required'
        super().__init__()
    
    def process(self, chain, reply:Reply, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Inject the groups identifiers.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        
        if reply.groups is None: reply.groups = set()
        reply.groups.update(self.groups)
