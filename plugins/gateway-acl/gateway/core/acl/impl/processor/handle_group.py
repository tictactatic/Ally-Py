'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the group handling.
'''

from ally.container import wire
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from gateway.api.group import Group
from gateway.core.acl.spec import ACTION_GET, ACTION_ADD, ACTION_DEL
import itertools

# --------------------------------------------------------------------

class ACLMethod(Context):
    '''
    The ACL method context.
    '''
    # ---------------------------------------------------------------- Defined
    allowed = defines(set, doc='''
    @rtype: set(string)
    The groups names that are allowed access for method.
    ''')

class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    value = defines(object, doc='''
    @rtype: object
    The value required.
    ''')
    # ---------------------------------------------------------------- Required
    action = requires(str)
    target = requires(object)
    method = requires(Context)
    forGroup = requires(str)
    
# --------------------------------------------------------------------

@setup(Handler, name='handleGroup')
class HandleGroup(HandlerProcessor):
    '''
    Implementation for a processor that provides the group handling.
    '''
    
    acl_groups = {
              'Anonymous': 'This group contains the services that can be accessed by anyone',
              }; wire.config('acl_groups', doc='''
    The allow access pattern place holders that are placed where a identifier is expected.''')
    
    def __init__(self):
        assert isinstance(self.acl_groups, dict), 'Invalid acl groups %s' % self.acl_groups
        super().__init__(ACLMethod=ACLMethod)

    def process(self, chain, solicit:Solicit, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the group handling.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        
        if solicit.forGroup is not None:
            if solicit.forGroup not in self.acl_groups: return chain.cancel()
            
        if solicit.target not in (Group, Group.Name):
            if solicit.forGroup and solicit.method:
                if not solicit.method.allowed or not solicit.forGroup in solicit.method.allowed: chain.cancel()
            return
        
        if solicit.action == ACTION_GET:
            if solicit.forGroup:
                if solicit.target == Group: solicit.value = self.create(solicit.forGroup)
                else: solicit.value = solicit.forGroup
                
            elif solicit.method:
                if not solicit.method.allowed: return chain.cancel()
                if solicit.target == Group: values = (self.create(name) for name in solicit.method.allowed)
                else: values = solicit.method.allowed
                if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
                else: solicit.value = values
                
            else:
                if solicit.target == Group: values = (self.create(name) for name in self.acl_groups)
                else: values = self.acl_groups.keys()
                if solicit.value is not None: solicit.value = itertools.chain(solicit.value, values)
                else: solicit.value = values
        
        elif solicit.action in (ACTION_ADD, ACTION_DEL):
            if solicit.target != Group or not solicit.forGroup or not solicit.method: return chain.cancel()
            assert isinstance(solicit.method, ACLMethod), 'Invalid method %s' % solicit.method
            
            if solicit.action == ACTION_ADD:
                if solicit.method.allowed is None: solicit.method.allowed = set()
                solicit.method.allowed.add(solicit.forGroup)
            else:
                if not solicit.method.allowed or solicit.forGroup not in solicit.method.allowed: return chain.cancel()
                solicit.method.allowed.remove(solicit.forGroup)
                
    # ----------------------------------------------------------------
    
    def create(self, name):
        '''
        Create the group.
        '''
        value = Group()
        value.Name = name
        value.Description = self.acl_groups[name]
        
        return value
