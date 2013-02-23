'''
Created on Feb 21, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Processor that populates the rights based on the RBAC structure.
'''

from acl.spec import TypeAcl
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed, Handler
from ally.support.sqlalchemy.session import SessionSupport
from collections import Iterable
from itertools import chain
from security.meta.right import RightMapped
from security.meta.right_type import RightTypeMapped
from security.rbac.core.spec import IRbacService

# --------------------------------------------------------------------

class Solicitation(Context):
    '''
    The solicitation context.
    '''
    # ---------------------------------------------------------------- Required
    rbacId = requires(int, doc='''
    @rtype: integer
    The id of the rbac to fetch the rights for.
    ''')
    types = requires(Iterable, doc='''
    @rtype: Iterable(TypeAcl)
    The ACL types to add the default rights for.
    ''')
    # ---------------------------------------------------------------- Defined
    rights = defines(Iterable, doc='''
    @rtype: Iterable(RightAcl)
    The default rights for the types.
    ''')
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='rbacPopulateRights')
class RbacPopulateRights(HandlerProcessorProceed, SessionSupport):
    '''
    Provides the handler that populates the rights based on RBAC structure.
    '''
    
    rbacService = IRbacService; wire.entity('rbacService')
    # Rbac service to use for complex role operations.
    
    def __init__(self):
        assert isinstance(self.rbacService, IRbacService), 'Invalid rbac service %s' % self.rbacService
        super().__init__()
    
    def process(self, solicitation:Solicitation, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Populate the rights.
        '''
        assert isinstance(solicitation, Solicitation), 'Invalid solicitation %s' % solicitation
        assert isinstance(solicitation.rbacId, int), 'Invalid rbac Id %s' % solicitation.rbacId
        
        allTypes = {aclType.name: aclType for aclType in solicitation.types}
        
        sql = self.session().query(RightMapped.Name, RightTypeMapped.Name).join(RightTypeMapped)
        sql = self.rbacService.rightsForRbacSQL(solicitation.rbacId, sql=sql)
        
        rights, types = [], {}
        for name, typeName in sql.all():
            aclType = types.get(typeName)
            if not aclType:
                aclType = allTypes.get(typeName)
                if not aclType: continue
                types[typeName] = aclType
            assert isinstance(aclType, TypeAcl)
            rights.extend(aclType.rightsFor(name))
            
        solicitation.types = types.values()
        if Solicitation.rights in solicitation:
            solicitation.rights = chain(solicitation.rights, rights)
        else:
            solicitation.rights = rights
