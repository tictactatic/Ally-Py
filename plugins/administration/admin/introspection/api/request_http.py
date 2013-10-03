'''
Created on Oct 1, 2013

@package: administration
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Nistor Gabriel

API specifications for the REST HTTP requests.
'''

from .model import Property
from admin.api.domain_admin import modelAdmin
from ally.api.config import query, call, service
from ally.api.criteria import AsLikeOrdered, AsEqualOrdered
from ally.api.option import SliceAndTotal # @UnusedImport
from ally.api.type import Iter

# --------------------------------------------------------------------

class Request:
    '''
    Provides the HTTP request specification.
    '''
    Id = int
    API = str
    Path = str
    Name = str
    Method = str
    Description = str
    
Request.ShadowOf = Request
Request = modelAdmin(Request, id='Id')

# --------------------------------------------------------------------

@query(Request)
class QRequest:
    '''
    Provides the request query.
    '''
    api = AsLikeOrdered
    path = AsLikeOrdered
    name = AsLikeOrdered
    method = AsEqualOrdered

# --------------------------------------------------------------------

@service
class IRequestHTTPService:
    '''
    Provides the HTTP requests API resources introspection available for the application.
    '''
    
    @call
    def getRequest(self, id:Request.Id) -> Request:
        '''
        Provides the request for the provided id.
        '''
        
    @call
    def getRequests(self, q:QRequest=None, **options:SliceAndTotal) -> Iter(Request.Id):
        '''
        Provides all the requests or filtered by the query.
        '''
        
    @call
    def getProperties(self, id:Request.Id) -> Iter(Property.API):
        '''
        Provides the properties for the provided request.
        '''
