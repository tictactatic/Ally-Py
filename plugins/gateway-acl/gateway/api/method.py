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
    def getMethods(self, access:Access=None) -> Iter(Method.Name):
        '''
        Provides the accesses methods.
        '''
