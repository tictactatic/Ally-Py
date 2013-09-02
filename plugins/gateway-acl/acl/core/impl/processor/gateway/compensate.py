'''
Created on Sep 2, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds the permissions based on ACL compensates.
'''

from acl.api.access import Access
from acl.api.compensate import Compensate
from acl.core.spec import ICompensateProvider
from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from collections import Iterable

# --------------------------------------------------------------------
  
class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Required
    permissions = requires(Iterable)
    acl = requires(object)

class PermissionCompensate(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Defined
    navigate = defines(str, doc='''
    @rtype: string
    The navigate path.
    ''')
    # ---------------------------------------------------------------- Required
    access = requires(Access)
    filters = requires(dict)
       
# --------------------------------------------------------------------

@injected
class RegisterCompensatePermissionHandler(HandlerProcessor):
    '''
    Provides the handler that adds the permissions based on ACL compensates.
    '''
    
    compensateProvider = ICompensateProvider
    # The ACL compensate provider.
    
    def __init__(self):
        assert isinstance(self.compensateProvider, ICompensateProvider), \
        'Invalid ACL compensate provider %s' % self.compensateProvider
        super().__init__()
    
    def process(self, chain, solicit:Solicit, Permission:PermissionCompensate, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the ACL compensates permissions.
        '''
        assert isinstance(solicit, Solicit), 'Invalid reply %s' % solicit
        if solicit.acl is None or solicit.permissions is None: return
        
        solicit.permissions = self.iteratePermissions(solicit.acl, solicit.permissions, Permission)

    # ----------------------------------------------------------------
    
    def iteratePermissions(self, acl, permissions, Permission):
        '''
        Iterate the compensate permissions for the acl.
        '''
        assert isinstance(permissions, Iterable), 'Invalid permissions %s' % permissions
        assert issubclass(Permission, PermissionCompensate), 'Invalid permission class %s' % Permission

        compensates, accessesIds = {}, set()
        for accessId, compensate, compensated in self.compensateProvider.iterateCompensates(acl):
            assert isinstance(accessId, int), 'Invalid access id %s' % accessId
            assert isinstance(compensate, Compensate), 'Invalid compensate %s' % compensate
            assert isinstance(compensated, Access), 'Invalid access %s' % compensated
            if compensated.Id in compensates: continue
            compensates[compensated.Id] = accessId, compensate, compensated
            accessesIds.add(accessId)

        compensators = {}
        for permission in permissions:
            assert isinstance(permission, PermissionCompensate), 'Invalid permission %s' % permission
            assert isinstance(permission.access, Access), 'Invalid access %s' % permission.access
            compensates.pop(permission.access.Id, None)
            if permission.access.Id in accessesIds: compensators[permission.access.Id] = permission
            yield permission
            
        for accessId, compensate, compensated in compensates.values():
            permission = compensators.get(accessId)
            if permission is None: continue
            
            cpermission = Permission()
            assert isinstance(cpermission, PermissionCompensate), 'Invalid permission %s' % cpermission
            cpermission.access = compensated
            cpermission.filters = {}
            cpermission.navigate = compensate.Path
            
            if permission.filters and compensate.Mapping:
                assert isinstance(permission.filters, dict), 'Invalid filters %s' % permission.filters
                for identifier, (entriesFilters, propertiesFilters) in permission.filters.items():
                    centriesFilters = {}
                    for position, paths in entriesFilters.items():
                        if position in compensate.Mapping: centriesFilters[compensate.Mapping[position]] = paths
                    cpermission.filters[identifier] = centriesFilters, propertiesFilters
            
            yield cpermission
        
