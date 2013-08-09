'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL method access.
'''

from ..api.group import Group
from ..api.method import IMethodService, Method
from ..core.acl.spec import IACLManagement
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup

# --------------------------------------------------------------------

@injected
@setup(IMethodService, name='methodService')
class MethodService(IMethodService):
    '''
    Implementation for @see: IMethodService that provides the ACL access method setup support.
    '''
    
    aclManagement = IACLManagement; wire.entity('aclManagement')
    
    def __init__(self):
        assert isinstance(self.aclManagement, IACLManagement), 'Invalid ACL management %s' % self.aclManagement
        
    def getById(self, name):
        '''
        @see: IMethodService.getById
        '''
        assert isinstance(name, str), 'Invalid method name %s' % name
        method = self.aclManagement.get(Method, forName=name)
        if not method: raise InvalidIdError()
        return method
        
    def getMethods(self, access=None, group=None, **options):
        '''
        @see: IMethodService.getMethods
        '''
        return sorted(self.aclManagement.get(Method.Name, forAccess=access, forGroup=group, forAll=True) or ())
    
    def getGroups(self, access, method):
        '''
        @see: IMethodService.getGroups
        '''
        return sorted(self.aclManagement.get(Group.Name, forAccess=access, forMethod=method) or ())
        
    def addMethod(self, access, group, method):
        '''
        @see: IMethodService.addMethod
        '''
        return self.aclManagement.add(Method, access=access, group=group, method=method)
        
    def removeMethod(self, access, group, method):
        '''
        @see: IMethodService.removeMethod
        '''
        return self.aclManagement.remove(Method, access=access, group=group, method=method)
