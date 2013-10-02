'''
Created on Aug 13, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for group gateway ACL.
'''

from .group import Group
from ally.api.config import service, call
from ally.api.type import Iter
from gateway.api.gateway import Gateway

# --------------------------------------------------------------------

@service
class IGatewayACLService:
    '''
    The gateway service that provides the gateways based on ACL group.
    '''

    @call
    def getGateways(self, group:Group) -> Iter(Gateway):
        '''
        Get the gateways for the ACL group.
        '''
