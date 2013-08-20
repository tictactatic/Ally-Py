'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for service access.
'''

from .domain_acl import modelACL
from ally.api.config import service, call, query
from ally.api.criteria import AsEqualOrdered
from ally.support.api.entity_ided import Entity, IEntityGetService, QEntity, \
    IEntityQueryService
from ally.api.type import List

# --------------------------------------------------------------------

class Access(Entity):
    '''
    Contains data required for mapping an ACL access.
        Path -       contains the path that the access maps to. The path contains beside the fixed string
                     names also markers '*' for where dynamic path elements are expected.
        Method -     the method name that this access maps to.
        Types -      the types list needs to have exactly as many entries as there are '*' in the access 'Path', and the
                     entries will indicate the type name expected for the corresponding '*' index in the access 'Path'.
        ShadowOf -   the access that this access is actually shadowing, this means that the access path is just a reroute
                     for the shadowed access.
    '''
    Path = str
    Method = str
    Types = List(str)

Access.ShadowOf = Access
Access = modelACL(Access)
 
# --------------------------------------------------------------------

@query(Access)
class QAccess(QEntity):
    '''
    Provides the query for access.
    '''
    path = AsEqualOrdered
    method = AsEqualOrdered

# --------------------------------------------------------------------

@service((Entity, Access), (QEntity, QAccess))
class IAccessService(IEntityGetService, IEntityQueryService):
    '''
    The ACL access service provides the means of setting up the access control layer for services.
    '''
    
    @call
    def insert(self, access:Access) -> Access.Id:
        '''
        Insert the access.
        
        @param access: Access
            The access to be inserted.
        @return: integer
            The id assigned to the access
        '''
    
    @call
    def delete(self, accessId:Access) -> bool:
        '''
        Delete the access for the provided id.
        
        @param id: integer
            The id of the access to be deleted.
        @return: boolean
            True if the delete is successful, false otherwise.
        '''
    
    # TODO: Gabriel: remove
    @call(filter='Filter1')
    def isDummy1Filter(self, accessId:Access) -> bool:
        '''
        '''
    
    @call(webName='Second', filter='Filter2')
    def isDummy2Filter(self, accessId:Access) -> bool:
        '''
        '''
