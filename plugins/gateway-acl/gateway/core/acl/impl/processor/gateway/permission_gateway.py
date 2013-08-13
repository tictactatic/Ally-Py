'''
Created on Aug 13, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds the Gateway objects based on permissions.
'''

from ally.container.support import setup
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from collections import Iterable
from gateway.api.gateway import Gateway
import itertools

# --------------------------------------------------------------------

class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    gateways = defines(Iterable, doc='''
    @rtype: Iterable(Gateway)
    The permission gateways.
    ''')
    # ---------------------------------------------------------------- Required
    permissions = requires(Iterable)

class Permission(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(str)
    method = requires(str)
    filtersPath = requires(dict)
     
# --------------------------------------------------------------------

@setup(Handler, name='registerPermissionGateways')
class RegisterPermissionGateways(HandlerProcessor):
    '''
    Provides the handler that adds the Gateway objects based on permissions.
    '''
    
    def __init__(self):
        super().__init__(Permission=Permission)
    
    def process(self, chain, reply:Reply, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the access gateways.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        if reply.permissions is None: return
        
        gateways = self.iterGateways(reply.permissions)
        if reply.gateways is not None: reply.gateways = itertools.chain(reply.gateways, gateways)
        else: reply.gateways = gateways

    # ----------------------------------------------------------------
    
    def iterGateways(self, permissions):
        '''
        Iterates the permissions gateways.
        '''
        assert isinstance(permissions, Iterable), 'Invalid permissions %s' % permissions
        for permission in permissions:
            assert isinstance(permission, Permission), 'Invalid permission %s' % permission
            
            gateway = Gateway()
            gateway.Pattern = permission.path
            gateway.Methods = [permission.method]
            if permission.filtersPath:
                gateway.Filters = []
                for key in sorted(permission.filtersPath):
                    gateway.Filters.append('|'.join(sorted(permission.filtersPath[key])))
                    
            yield gateway
