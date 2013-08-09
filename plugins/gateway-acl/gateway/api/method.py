'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for method access.
'''

from .access import Access
from .domain_acl import modelACL
from .group import Group
from ally.api.config import service, call
from ally.api.type import Iter
from ally.support.api.entity_named import Entity, IEntityGetService

# --------------------------------------------------------------------

@modelACL
class Method(Entity):
    '''
    Defines an access method entry.
    '''

# --------------------------------------------------------------------

@service((Entity, Method))
class IMethodService(IEntityGetService):
    '''
    The ACL method access service provides the means of setting up the method access.
    '''
    
    @call
    def getMethods(self, access:Access=None, group:Group=None) -> Iter(Method.Name):
        '''
        Provides the accesses methods.
        '''
        
    @call
    def getGroups(self, access:Access, method:Method) -> Iter(Group.Name):
        '''
        Provides the accesses groups for method.
        '''
    
    @call
    def addMethod(self, access:Access.Name, group:Group.Name, method:Method.Name) -> bool:
        '''
        Adds a new method for the access group.
        '''
        
    @call
    def removeMethod(self, access:Access, group:Group, method:Method) -> bool:
        '''
        Removes the method for the access group.
        '''
