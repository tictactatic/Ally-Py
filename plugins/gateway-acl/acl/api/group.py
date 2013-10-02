'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for access group.
'''

from .domain_acl import modelACL
from acl.api.acl import IAclPrototype
from acl.api.compensate import ICompensatePrototype
from ally.api.config import service, query
from ally.api.criteria import AsBooleanOrdered
from ally.api.option import SliceAndTotal # @UnusedImport
from ally.support.api.entity_named import Entity, IEntityService, QEntity

# --------------------------------------------------------------------

@modelACL
class Group(Entity):
    '''
    Defines the group of ACL access.
        Name -           the group unique name.
        IsAnonymous -    if true it means that the group should be delivered for anonymous access.
        Description -    a description explaining the group.
    '''
    IsAnonymous = bool
    Description = str

# --------------------------------------------------------------------

@query(Group)
class QGroup(QEntity):
    '''
    Provides the query for group.
    '''
    isAnonymous = AsBooleanOrdered
    
# --------------------------------------------------------------------

@service((Entity, Group), (QEntity, QGroup), ('ACL', Group))
class IGroupService(IEntityService, IAclPrototype, ICompensatePrototype):
    '''
    The ACL access group service used for allowing accesses based on group.
    '''
   
