'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL access.
'''

from ..api.access import Access, IAccessService
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines
from ally.support.api.util_service import processCollection
from gateway.core.acl.impl.base import RequireSolicit, getSolicit

# --------------------------------------------------------------------

class Solicit(RequireSolicit):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    forAccess = defines(str, doc='''
    @rtype: string
    The access name to get.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(IAccessService, name='accessService')
class AccessService(IAccessService):
    '''
    Implementation for @see: IAccessService that provides the ACL access support.
    '''
    
    assemblyAccessManagement = Assembly; wire.entity('assemblyAccessManagement')
    # The assembly to be used for managing access.
    
    def __init__(self):
        assert isinstance(self.assemblyAccessManagement, Assembly), \
        'Invalid assembly management %s' % self.assemblyAccessManagement
        self._manage = self.assemblyAccessManagement.create(solicit=Solicit)
    
    def getById(self, name):
        '''
        @see: IAccessService.getById
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        access = getSolicit(self._manage, Access, forAccess=name)
        if not access: raise InvalidIdError()
        return access
    
    def getAll(self, **options):
        '''
        @see: IAccessService.getAll
        '''
        return processCollection(sorted(getSolicit(self._manage, Access.Name) or ()), **options)
    
    # TODO: remove    
    def isDummy1Filter(self, id):
        print(id)
        return id == '00000000'
    
    # TODO: remove    
    def isDummy2Filter(self, id):
        print(id)
        return id == '2036D140'
