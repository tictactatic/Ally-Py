'''
Created on Aug 8, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL method access.
'''

from . import access
from ..api.method import IMethodService, Method
from ally.api.error import InvalidIdError
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines
from gateway.core.acl.impl.base import getSolicit

# --------------------------------------------------------------------

class Solicit(access.Solicit):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Defined
    forMethod = defines(str, doc='''
    @rtype: string
    The method name to be handled.
    ''')
    
# --------------------------------------------------------------------
    
@injected
@setup(IMethodService, name='methodService')
class MethodService(IMethodService):
    '''
    Implementation for @see: IMethodService that provides the ACL access method setup support.
    '''
    
    assemblyMethodManagement = Assembly; wire.entity('assemblyMethodManagement')
    # The assembly to be used for managing methods.
    
    def __init__(self):
        assert isinstance(self.assemblyMethodManagement, Assembly), \
        'Invalid assembly management %s' % self.assemblyMethodManagement
        self._manage = self.assemblyMethodManagement.create(solicit=Solicit)
        
    def getById(self, name):
        '''
        @see: IMethodService.getById
        '''
        assert isinstance(name, str), 'Invalid method name %s' % name
        method = getSolicit(self._manage, Method, forMethod=name)
        if not method: raise InvalidIdError()
        return method
        
    def getMethods(self, access=None):
        '''
        @see: IMethodService.getMethods
        '''
        return sorted(getSolicit(self._manage, Method.Name, forAccess=access) or ())
