'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL filters.
'''

from ..api.filter import Filter, IFilterService
from ..core.acl.spec import IACLManagement
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.support.api.util_service import processCollection

# --------------------------------------------------------------------

@injected
@setup(IFilterService, name='filterService')
class FilterService(IFilterService):
    '''
    Implementation for @see: IFilterService that provides the ACL access setup support.
    '''
    
    aclManagement = IACLManagement; wire.entity('aclManagement')
    
    def __init__(self):
        assert isinstance(self.aclManagement, IACLManagement), 'Invalid ACL management %s' % self.aclManagement
    
    def getById(self, name):
        '''
        @see: IFilterService.getById
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        filter = self.aclManagement.get(Filter, forFilter=name)
        if not filter: raise InvalidIdError()
        return filter
        
    def getAll(self, **options):
        '''
        @see: IFilterService.getAll
        '''
        return processCollection(self.aclManagement.get(Filter.Name), **options)
    
    def getFilters(self, access, method, group):
        '''
        @see: IFilterService.getFilters
        '''
        assert isinstance(access, str), 'Invalid access name %s' % access
        assert isinstance(method, str), 'Invalid method name %s' % method
        assert isinstance(group, str), 'Invalid group name %s' % group
        return sorted(self.aclManagement.get(Filter.Name, forAccess=access, forMethod=method, forGroup=group) or ())
    
    def addFilter(self, access, method, group, filter):
        '''
        @see: IFilterService.addFilter
        '''
        return self.aclManagement.add(Filter, forAccess=access, forMethod=method, forGroup=group, forFilter=filter)
        
    def removeFilter(self, access, method, group, filter):
        '''
        @see: IFilterService.removeFilter
        '''
        return self.aclManagement.remove(Filter, forAccess=access, forMethod=method, forGroup=group, forFilter=filter)
        
