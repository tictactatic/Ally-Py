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
        filter = self.aclManagement.get(Filter, name)
        if not filter: raise InvalidIdError()
        return filter
        
    def getAll(self, **options):
        '''
        @see: IFilterService.getAll
        '''
        return processCollection(self.aclManagement.get(Filter.Name, forAll=True), **options)
    
    def getFilters(self, access, group=None, method=None):
        '''
        @see: IFilterService.getFilters
        '''
        return sorted(self.aclManagement.get(Filter.Name, forAccess=access, forGroup=group, forMethod=method) or ())
    
    def addFilter(self, access, group, method, filter):
        '''
        @see: IFilterService.addFilter
        '''
        return self.aclManagement.add(Filter, access=access, group=group, method=method, filter=filter)
        
    def removeFilter(self, access, group, method, filter):
        '''
        @see: IFilterService.removeFilter
        '''
        return self.aclManagement.remove(Filter, access=access, group=group, method=method, filter=filter)
        
