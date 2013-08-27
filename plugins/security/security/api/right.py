'''
Created on Dec 21, 2012

@package: security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for security right.
'''

from .domain_security import modelSecurity
from .right_type import RightType
from ally.api.config import query, service, call
from ally.api.criteria import AsLikeOrdered
from ally.api.option import SliceAndTotal # @UnusedImport
from ally.api.type import Iter
from ally.support.api.entity import IEntityGetPrototype, IEntityCRUDPrototype

# --------------------------------------------------------------------

@modelSecurity(id='Id')
class Right:
    '''
    Provides the right data.
    '''
    Id = int
    Type = RightType
    Name = str
    Description = str

# --------------------------------------------------------------------

@query(Right)
class QRight:
    '''
    Query for right service
    '''
    name = AsLikeOrdered

# --------------------------------------------------------------------

@service(('Entity', Right))
class IRightService(IEntityGetPrototype, IEntityCRUDPrototype):
    '''
    Right model service API.
    '''
    
    @call
    def getAll(self, typeName:RightType=None, q:QRight=None, **options:SliceAndTotal) -> Iter(Right.Id):
        '''
        Provides the rights searched by the provided query.
        '''
