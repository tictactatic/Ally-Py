'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL groups.
'''

from ..api.group import IGroupService, Group
from ..core.acl.spec import IACLManagement
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.support.api.util_service import processCollection

# --------------------------------------------------------------------

@injected
@setup(IGroupService, name='groupService')
class GroupService(IGroupService):
    '''
    Implementation for @see: IGroupService that provides the ACL access groups.
    '''
              
    aclManagement = IACLManagement; wire.entity('aclManagement')
    
    def __init__(self):
        assert isinstance(self.aclManagement, IACLManagement), 'Invalid ACL management %s' % self.aclManagement
        
    def getById(self, name):
        '''
        @see: IGroupService.getById
        '''
        assert isinstance(name, str), 'Invalid group name %s' % name
        group = self.aclManagement.get(Group, forGroup=name)
        if not group: raise InvalidIdError()
        return group
    
    def getAll(self, **options):
        '''
        @see: IGroupService.getAll
        '''
        return processCollection(sorted(self.aclManagement.get(Group.Name) or ()), **options)
    
    def getAllowed(self, access, method):
        '''
        @see: IGroupService.getAllowed
        '''
        assert isinstance(access, str), 'Invalid access name %s' % access
        assert isinstance(method, str), 'Invalid method name %s' % method
        return sorted(self.aclManagement.get(Group.Name, forAccess=access, forMethod=method) or ())
    
    def addGroup(self, access, method, group):
        '''
        @see: IGroupService.addGroup
        '''
        return self.aclManagement.add(Group, forAccess=access, forMethod=method, forGroup=group)
        
    def removeGroup(self, access, method, group):
        '''
        @see: IGroupService.removeGroup
        '''
        return self.aclManagement.remove(Group, forAccess=access, forMethod=method, forGroup=group)

