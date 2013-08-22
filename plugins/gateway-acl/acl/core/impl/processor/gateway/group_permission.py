'''
Created on Aug 21, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that adds the permissions based on ACL group structure.
'''

from acl.api.access import Access
from acl.meta.access import AccessMapped
from acl.meta.acl_intern import Path
from acl.meta.filter import FilterMapped
from acl.meta.group import AccessToGroup, GroupMapped, FilterToEntry, \
    FilterToProperty
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.support.sqlalchemy.session import SessionSupport
from collections import Iterable
import itertools

# --------------------------------------------------------------------

@setup(name='groupPermissionProvider')
class GroupPermissionProviderAlchemy(SessionSupport):
    '''
    The SQL alchemy database ACL group permission provider.
    '''
    
    def iteratePermissions(self, groups, Permission):
        '''
        Iterates all the group permissions.
        
        @param groups: set(string)
            The groups names to iterate the permissions for.
        @param Permission: ContextMetaClass
            The permission class to use for creating permission instance.
        @return: Iterable(Context)
            The permissions for the groups.
        '''
        assert issubclass(Permission, PermissionGroup), 'Invalid permission class %s' % Permission 
        
        sqlQuery = self.session().query(AccessMapped, GroupMapped.id, FilterMapped, FilterToEntry.position, FilterToProperty.name)
        sqlQuery = sqlQuery.select_from(AccessToGroup)
        sqlQuery = sqlQuery.join(AccessMapped).join(Path).join(GroupMapped)
        sqlQuery = sqlQuery.outerjoin(FilterToEntry).outerjoin(FilterToProperty).outerjoin(FilterMapped)
        sqlQuery = sqlQuery.filter(GroupMapped.Name.in_(groups)).order_by(Path.priority, AccessToGroup.accessId)
        
        current, ifilters = None, None
        for access, groupId, filtre, position, name in sqlQuery.yield_per(10):
            assert isinstance(access, AccessMapped), 'Invalid access %s' % access
            
            if current and current != access:
                yield Permission(access=current, filters=ifilters)
                current = None
            if current is None: current, ifilters = access, {}
            
            gfilters = ifilters.get(groupId)
            if gfilters is None: gfilters = ifilters[groupId] = {}, {}
            if filtre:
                assert isinstance(filtre, FilterMapped), 'Invalid filter %s' % filtre
                pathsEntry, pathsProperty = gfilters
                
                if position is not None:
                    paths = pathsEntry.get(position)
                    if paths is None: paths = pathsEntry[position] = set()
                    paths.update(filtre.Paths)
                
                if name is not None:
                    paths = pathsProperty.get(name)
                    if paths is None: paths = pathsProperty[name] = set()
                    paths.update(filtre.Paths)
        
        if current: yield Permission(access=current, filters=ifilters)
        
# --------------------------------------------------------------------
    
class Reply(Context):
    '''
    The reply context.
    '''
    # ---------------------------------------------------------------- Defined
    permissions = defines(Iterable, doc='''
    @rtype: Iterable(Context)
    The ACL permissions.
    ''')
    # ---------------------------------------------------------------- Required
    groups = requires(set)

class PermissionGroup(Context):
    '''
    The permission context.
    '''
    # ---------------------------------------------------------------- Defined
    access = defines(Access, doc='''
    @rtype: Access
    The ACL access associated with the permission.
    ''')
    filters = defines(dict, doc='''
    @rtype: dictionary{object: tuple(dictionary{integer:list[string]}, dictionary{string:list[string]})}
    The filters dictionary contains:
        identifier: (filter paths for entries indexed by entry position, filter paths for properties indexed by property name)
    ''')
       
# --------------------------------------------------------------------

@injected
@setup(Handler, name='registerGroupPermission')
class RegisterGroupPermissionHandler(HandlerProcessor):
    '''
    Provides the handler that adds the permissions based on ACL group database structure.
    '''
    
    groupPermissionProvider = GroupPermissionProviderAlchemy; wire.entity('groupPermissionProvider')
    
    def __init__(self):
        assert isinstance(self.groupPermissionProvider, GroupPermissionProviderAlchemy), \
        'Invalid group permission provider %s' % self.groupPermissionProvider
        super().__init__()
    
    def process(self, chain, reply:Reply, Permission:PermissionGroup, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Adds the group access permissions.
        '''
        assert isinstance(reply, Reply), 'Invalid reply %s' % reply
        if not reply.groups: return
        
        permissions = self.groupPermissionProvider.iteratePermissions(reply.groups, Permission)
        if reply.permissions is not None: reply.permissions = itertools.chain(reply.permissions, permissions)
        else: reply.permissions = permissions

