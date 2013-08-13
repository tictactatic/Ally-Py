'''
Created on Aug 14, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that injects groups identifiers.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from collections import Iterable
from gateway.api.group import Group
import itertools

# --------------------------------------------------------------------

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    identifiers = defines(Iterable, doc='''
    @rtype: Iterable(object)
    The identifiers created based on ACL groups.
    ''')
    
# --------------------------------------------------------------------

@injected
class GroupIdentifierHandler(HandlerProcessor):
    '''
    Provides the handler that injects groups identifiers.
    '''
    
    aclGroups = set
    # The groups names to inject into the reply identifiers.
    
    def __init__(self):
        assert isinstance(self.aclGroups, set), 'Invalid ACL groups %s' % self.aclGroups
        assert self.aclGroups, 'At least an ACL group is required'
        super().__init__()
    
    def process(self, chain, reply:Reply, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Inject the groups identifiers.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        
        identifiers = [(Group, name) for name in self.aclGroups]
        if reply.identifiers is not None: reply.identifiers = itertools.chain(reply.identifiers, identifiers)
        else: reply.identifiers = identifiers
