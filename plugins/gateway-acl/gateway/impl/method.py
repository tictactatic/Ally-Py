'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL method access.
'''

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
        method = self.aclManagement.get(Method, forMethod=name)
        if not method: raise InvalidIdError()
        return method
        
    def getMethods(self, access=None):
        '''
        @see: IMethodService.getMethods
        '''
        return sorted(self.aclManagement.get(Method.Name, forAccess=access) or ())
