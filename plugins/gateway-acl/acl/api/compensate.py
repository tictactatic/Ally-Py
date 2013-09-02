'''
Created on Sep 2, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for ACL access compensate.
'''

from .access import Access
from .domain_acl import modelACL
from ally.api.config import prototype, DELETE
from ally.api.type import Iter, Dict
from ally.support.api.util_service import modelId
import abc  # @UnusedImport

# --------------------------------------------------------------------

@modelACL
class Compensate:
    '''
    Contains data required for an ACL access compensate.
        Access -     the access that is being compensated.
        Path -       contains the path that the access maps to. The path contains beside the fixed string
                     names also markers like {1}, {2} ... {n} which represent the positions from the compensated request
                     path where values need to be placed.
        Mapping -    the mapping of positions, as a key the compensating access position and as a value the corresponding
                     compensated access position.
    '''
    Access = Access
    Path = str
    Mapping = Dict(int, int)

# --------------------------------------------------------------------

class ICompensatePrototype(metaclass=abc.ABCMeta):
    '''
    The ACL compensate access prototype service used to compensate lack of accesses.
    '''
    
    @prototype
    def getCompensates(self, identifier:lambda p:p.ACL, accessId:Access.Id) -> Iter(Compensate):
        '''
        Provides the compensated accesses for the provided access id.
        
        @param identifier: object
            The ACL object identifier.
        @param accessId: integer
            The access id that compensates.
         @return: Iterable(Compensate)
            An iterator containing the compensated accesses.
        '''
        
    @prototype(webName='Compensate')
    def addCompensate(self, identifier:lambda p: modelId(p.ACL), accessId:Access.Id, compensatedId:Access.Id):
        '''
        Adds the compensated access for the provided access id.

        @param identifier: object
            The ACL object identifier.
        @param accessId: integer
            The access id that compensates.
        @param compensatedId: integer
            The access id that is compensated.
        '''
        
    @prototype(method=DELETE, webName='Compensate')
    def remCompensate(self, identifier:lambda p: modelId(p.ACL), accessId:Access.Id, compensatedId:Access.Id) -> bool:
        '''
        Removes the compensated access for the provided access id
        
        @param identifier: object
            The ACL object identifier.
        @param accessId: integer
            The access id that compensates.
        @param compensatedId: integer
            The access id that is compensated.
        @return: boolean
            True if any compensated has been removed, False otherwise.
        '''
