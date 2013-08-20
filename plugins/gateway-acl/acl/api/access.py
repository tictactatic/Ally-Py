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
from binascii import crc32
from ally.api.type import List, Iter

# --------------------------------------------------------------------

class Access(Entity):
    '''
    Contains data required for mapping an ACL access.
        Path -       contains the path that the access maps to. The path contains beside the fixed string
                     names also markers '*' for where dynamic path elements are expected.
        Method -     the method name that this access maps to.
        ShadowOf -   the access that this access is actually shadowing, this means that the access path is just a reroute
                     for the shadowed access.
        Hash -       the hash that represents the full aspect of the access.
    '''
    Path = str
    Method = str
    Hash = str
    
Access.ShadowOf = Access
Access = modelACL(Access)

@modelACL(name=Access)
class Construct(Access):
    '''
    Contains data required for constructing an ACL access.
        Types -      the types list needs to have exactly as many entries as there are '*' in the access 'Path', and the
                     entries will indicate the type name expected for the corresponding '*' index in the access 'Path'.
    '''
    Types = List(str)

@modelACL(id='Position')
class Entry:
    '''
    The path entry that corresponds to a '*' dynamic path input.
    
    Position -       the position of the entry in the access path.
    Type -           the type name associated with the path entry.
    '''
    Position = int
    Type = str
   
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
    def getEntry(self, accessId:Access, position:Entry) -> Entry:
        '''
        Provides the path dynamic entry for access and position.
        '''
        
    @call
    def getEntries(self, accessId:Access) -> Iter(Entry.Position):
        '''
        Provides the path dynamic entries for access.
        '''
    
    @call
    def insert(self, access:Construct) -> Access.Id:
        '''
        Insert the access.
        
        @param access: Construct
            The access Construct to be inserted.
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
        
# --------------------------------------------------------------------

def generateId(path, method):
    '''
    Generates a unique id for the provided path and method.
    
    @param path: string
        The path to generate the id for.
    @param method: string
        The method name.
    @return: integer
        The generated hash id.
    '''
    assert isinstance(path, str), 'Invalid path %s' % path
    assert isinstance(method, str), 'Invalid method %s' % method
    return crc32(method.strip().upper().encode(), crc32(path.strip().strip('/').encode(), 0))

def generateHash(access):
    '''
    Generates a unique has for the provided construct access.
    
    @param access: Construct
        The construct access to generate the has for.
    @return: string
        The generated hash.
    '''
    assert isinstance(access, Construct), 'Invalid access %s' % access
    
    hashAcc = generateId(access.Path, access.Method) + (access.ShadowOf or 0)
    if access.Types:
        for name in sorted(access.Types): hashAcc = crc32(name.encode(), hashAcc)
    
    return ('%x' % hashAcc).upper()
