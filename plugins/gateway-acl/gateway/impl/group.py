'''
Created on Aug 7, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL groups.
'''

from . import method
from ..api.group import IGroupService, Group
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines
from ally.support.api.util_service import processCollection
from gateway.core.acl.impl.base import getSolicit, addSolicit, remSolicit

# --------------------------------------------------------------------

class Solicit(method.Solicit):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    forGroup = defines(str, doc='''
    @rtype: string
    The group name to be handled.
    ''')

# --------------------------------------------------------------------

@injected
@setup(IGroupService, name='groupService')
class GroupService(IGroupService):
    '''
    Implementation for @see: IGroupService that provides the ACL access groups.
    '''
    
    assemblyGroupManagement = Assembly; wire.entity('assemblyGroupManagement')
    # The assembly to be used for managing groups.
    
    def __init__(self):
        assert isinstance(self.assemblyGroupManagement, Assembly), \
        'Invalid assembly management %s' % self.assemblyGroupManagement
        self._manage = self.assemblyGroupManagement.create(solicit=Solicit)
        
    def getById(self, name):
        '''
        @see: IGroupService.getById
        '''
        assert isinstance(name, str), 'Invalid group name %s' % name
        group = getSolicit(self._manage, Group, forGroup=name)
        if not group: raise IdError()
        return group
    
    def getAll(self, **options):
        '''
        @see: IGroupService.getAll
        '''
        return processCollection(sorted(getSolicit(self._manage, Group.Name) or ()), **options)
    
    def getAllowed(self, access, method):
        '''
        @see: IGroupService.getAllowed
        '''
        assert isinstance(access, str), 'Invalid access name %s' % access
        assert isinstance(method, str), 'Invalid method name %s' % method
        return sorted(getSolicit(self._manage, Group.Name, forAccess=access, forMethod=method) or ())
    
    def addGroup(self, access, method, group):
        '''
        @see: IGroupService.addGroup
        '''
        return addSolicit(self._manage, Group, forAccess=access, forMethod=method, forGroup=group)
        
    def removeGroup(self, access, method, group):
        '''
        @see: IGroupService.removeGroup
        '''
        return remSolicit(self._manage, Group, forAccess=access, forMethod=method, forGroup=group)

