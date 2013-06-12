'''
Created on Jun 12, 2013

@package: example user
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Martin Saturka

Simple implementation for the user type APIs.
'''

from example.user.api.user_type import IUserTypeService, QUserType
from example.user.meta.user_type import UserTypeMapped
from sql_alchemy.impl.entity import EntityServiceAlchemy
from ally.container.ioc import injected
from ally.container.support import setup

# --------------------------------------------------------------------
@injected
@setup(IUserTypeService, name='userTypeService')
class UserTypeServiceAlchemy(EntityServiceAlchemy, IUserTypeService):
    '''
    Implementation for @see: IUserTypeService
    '''

    def __init__(self):
        EntityServiceAlchemy.__init__(self, UserTypeMapped, QUserType)

