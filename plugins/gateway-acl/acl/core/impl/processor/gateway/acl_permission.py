'''
Created on Aug 21, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds the permissions based on ACL structure.
'''

from acl.api.access import Access
from acl.core.spec import IAclPermissionProvider
from ally.container.ioc import injected
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from collections import Iterable
import itertools

# --------------------------------------------------------------------
  
class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    permissions = defines(Iterable, doc='''
    @rtype: Iterable(Context)
    The ACL permissions.
    ''')
    # ---------------------------------------------------------------- Required
    identifiers = requires(Iterable)

class PermissionAcl(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Defined
    access = defines(Access, doc='''
    @rtype: Access
    The ACL access associated with the permission.
    ''')
    filters = defines(dict, doc='''
    @rtype: dictionary{object: tuple(dictionary{integer:list[string]}, dictionary{string:list[string]})}
    The filters dictionary contains:
        identifier: (filter paths for entries indexed by entry position, filter paths for properties indexed by property name)
    ''')
       
# --------------------------------------------------------------------

@injected
class RegisterAclPermissionHandler(HandlerProcessor):
    '''
    Provides the handler that adds the permissions based on ACL structure.
    '''
    
    aclPermissionProvider = IAclPermissionProvider
    # The ACL permission provider.
    
    def __init__(self):
        assert isinstance(self.aclPermissionProvider, IAclPermissionProvider), \
        'Invalid ACL permission provider %s' % self.aclPermissionProvider
        super().__init__()
    
    def process(self, chain, reply:Reply, Permission:PermissionAcl, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the ACL access permissions.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        if reply.identifiers is None: return
        
        permissions = self.iteratePermissions(reply.identifiers, Permission)
        if reply.permissions is not None: reply.permissions = itertools.chain(reply.permissions, permissions)
        else: reply.permissions = permissions

    # ----------------------------------------------------------------
    
    def iteratePermissions(self, identifiers, Permission):
        '''
        Iterate the permissions for the identifiers.
        '''
        assert issubclass(Permission, PermissionAcl), 'Invalid permission class %s' % Permission
        
        for access, filters in self.aclPermissionProvider.iteratePermissions(identifiers):
            assert isinstance(access, Access), 'Invalid access %s' % access
            assert isinstance(filters, dict), 'Invalid filters %s' % filters
            yield Permission(access=access, filters=filters)
