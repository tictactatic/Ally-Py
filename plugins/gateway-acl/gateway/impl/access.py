'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL access.
'''

from ..api.access import Access, IAccessService
from ..core.acl.spec import IACLManagement
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.support.api.util_service import processCollection

# --------------------------------------------------------------------

@injected
@setup(IAccessService, name='accessService')
class AccessService(IAccessService):
    '''
    Implementation for @see: IAccessService that provides the ACL access support.
    '''
    
    aclManagement = IACLManagement; wire.entity('aclManagement')
    
    def __init__(self):
        assert isinstance(self.aclManagement, IACLManagement), 'Invalid ACL management %s' % self.aclManagement
    
    def getById(self, name):
        '''
        @see: IAccessService.getById
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        access = self.aclManagement.get(Access, forAccess=name)
        if not access: raise InvalidIdError()
        return access
    
    def getAll(self, **options):
        '''
        @see: IAccessService.getAll
        '''
        return processCollection(sorted(self.aclManagement.get(Access.Name) or ()), **options)
    
    # TODO: remove    
    def isDummy1Filter(self, id):
        print(id)
        return id == '00000000'
    
    # TODO: remove    
    def isDummy2Filter(self, id):
        print(id)
        return id == '2036D140'
