'''
Created on Aug 9, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds the Gateway objects for configured access.
'''

from ally.api.type import Type
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from collections import Iterable
from gateway.api.gateway import Gateway
import itertools
import re

# --------------------------------------------------------------------

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    gateways = defines(Iterable, doc='''
    @rtype: Iterable(Gateway)
    The access gateways.
    ''')

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    accesses = requires(dict)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    
class ACLAccess(Context):
    '''
    The ACL access context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(list)
    methods = requires(dict)

class ACLMethod(Context):
    '''
    The ACL method context.
    '''
    # ---------------------------------------------------------------- Required
    allowed = requires(set)
    invoker = requires(Context)
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='registerAccessGateways')
class RegisterAccessGateways(HandlerProcessor):
    '''
    Provides the handler that adds the Gateway objects for configured access.
    '''
    
    root_uri = ''
    # The root_uri to add to the pattern paths
    acl_groups = ['Anonymous']; wire.config('acl_groups', doc='''
    The acl access groups to provide gateways for.''')
    
    def __init__(self):
        '''
        Construct the default gateways register.
        '''
        assert isinstance(self.root_uri, str), 'Invalid root uri %s' % self.root_uri
        assert isinstance(self.acl_groups, list), 'Invalid acl groups %s' % self.acl_groups
        assert self.acl_groups, 'At least an acl group is required'
        super().__init__(Node=Node, ACLAccess=ACLAccess, ACLMethod=ACLMethod)
        
        self._groups = set(self.acl_groups)
    
    def process(self, chain, reply:Reply, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the access gateways.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.accesses: return
        assert isinstance(register.accesses, dict), 'Invalid register accesses %s' % register.accesses
        
        gateways = []
        for access in register.accesses.values():
            assert isinstance(access, ACLAccess), 'Invalid access %s' % access
            if not access.methods: continue
            assert isinstance(access.methods, dict), 'Invalid methods %s' % access.methods
            
            methods = []
            for name, method in access.methods.items():
                assert isinstance(method, ACLMethod), 'Invalid method %s' % method
                if not method.allowed or self._groups.isdisjoint(method.allowed): continue
                methods.append(name)
            
            if methods:
                gateway = Gateway()
                gateways.append(gateway)
                
                path = []
                if self.root_uri: path.append(self.root_uri)
                for el in access.path:
                    if isinstance(el, str): path.append(re.escape(el))
                    else:
                        assert isinstance(el, Node), 'Invalid node %s' % el
                        assert isinstance(el.type, Type), 'Invalid type %s' % el.type
                        if el.type.isOf(int): path.append('([0-9\\-]+)')
                        else: path.append('([^\\/]+)')
                
                gateway.Pattern = '%s[\\/]?(?:\\.|$)' % '\\/'.join(path)
                gateway.Methods = methods

        if reply.gateways is not None: reply.gateways = itertools.chain(reply.gateways, gateways)
        else: reply.gateways = gateways
