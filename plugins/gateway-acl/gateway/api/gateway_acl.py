'''
Created on Aug 13, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for gateway ACL.
'''

from .gateway import Gateway
from .group import Group
from ally.api.config import service, call
from ally.api.type import Iter

# --------------------------------------------------------------------

@service
class IGatewayACLService:
    '''
    The gateway service that provides the gateways based on ACL.
    '''

    @call
    def getGateways(self, group:Group) -> Iter(Gateway):
        '''
        Get the gateways for the ACL group.
        '''
        
        #TODO: Gabriel: see below
        # Vezi ca nu ii buna combinarea de filtre.
#        fa dupa aia filter pattern hint.
#        dupa aia sa incepi cu right based access.
#        si dupa aia cu action
#        si numa dupa aia cu model filter
