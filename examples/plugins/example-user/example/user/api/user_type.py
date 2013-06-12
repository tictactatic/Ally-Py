'''
Created on Jun 12, 2013

@package: example user
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Martin Saturka

The API descriptions for user type sample.
'''

from ally.api.config import query, service
from ally.api.criteria import AsLike
from example.api.domain_example import modelExample
from ally.support.api.entity import Entity, QEntity, IEntityService

# --------------------------------------------------------------------

@modelExample
class UserType(Entity):
    '''
    The user type model.
    '''
    Name = str

# --------------------------------------------------------------------

@query(UserType)
class QUserType(QEntity):
    '''
    The user type model query object.
    '''
    name = AsLike

# --------------------------------------------------------------------

@service((Entity, UserType), (QEntity, QUserType))
class IUserTypeService(IEntityService):
    '''
    The user type service.
    '''
