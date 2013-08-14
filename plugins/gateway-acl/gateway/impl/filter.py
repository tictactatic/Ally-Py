'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL filters.
'''

from . import group
from ..api.filter import Filter, IFilterService
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines
from ally.support.api.util_service import processCollection
from gateway.core.acl.impl.base import getSolicit, addSolicit, remSolicit

# --------------------------------------------------------------------

class Solicit(group.Solicit):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    forFilter = defines(str, doc='''
    @rtype: string
    The filter name to be handled.
    ''')
    filterHint = defines(str, doc='''
    @rtype: string
    The filter placing hint.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(IFilterService, name='filterService')
class FilterService(IFilterService):
    '''
    Implementation for @see: IFilterService that provides the ACL access setup support.
    '''
    
    assemblyFilterManagement = Assembly; wire.entity('assemblyFilterManagement')
    # The assembly to be used for managing groups.
    
    def __init__(self):
        assert isinstance(self.assemblyFilterManagement, Assembly), \
        'Invalid assembly management %s' % self.assemblyFilterManagement
        self._manage = self.assemblyFilterManagement.create(solicit=Solicit)
    
    def getById(self, name):
        '''
        @see: IFilterService.getById
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        filter = getSolicit(self._manage, Filter, forFilter=name)
        if not filter: raise InvalidIdError()
        return filter
        
    def getAll(self, **options):
        '''
        @see: IFilterService.getAll
        '''
        return processCollection(getSolicit(self._manage, Filter.Name), **options)
    
    def getFilters(self, access, method, group):
        '''
        @see: IFilterService.getFilters
        '''
        assert isinstance(access, str), 'Invalid access name %s' % access
        assert isinstance(method, str), 'Invalid method name %s' % method
        assert isinstance(group, str), 'Invalid group name %s' % group
        return sorted(getSolicit(self._manage, Filter.Name, forAccess=access, forMethod=method, forGroup=group) or ())
    
    def addFilter(self, access, method, group, filter, hint=None):
        '''
        @see: IFilterService.addFilter
        '''
        return addSolicit(self._manage, Filter, forAccess=access, forMethod=method, forGroup=group,
                          forFilter=filter, filterHint=hint)
        
    def removeFilter(self, access, method, group, filter):
        '''
        @see: IFilterService.removeFilter
        '''
        return remSolicit(self._manage, Filter, forAccess=access, forMethod=method, forGroup=group, forFilter=filter)
        
