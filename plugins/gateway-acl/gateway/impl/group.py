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
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.api.error import InvalidIdError

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
        group = self.aclManagement.get(Group, forName=name)
        if not group: raise InvalidIdError()
        return group
    
    def getGroups(self, access=None):
        '''
        @see: IGroupService.getGroups
        '''
        return sorted(self.aclManagement.get(Group.Name, forAccess=access, forAll=True) or ())
