'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL access.
'''

from ..api.access import IAccessService, Access, QAccess
from ..meta.access import AccessMapped, AccessToType
from ..meta.acl_intern import Path, Method, Type
from acl.core.spec import generateId
from ally.api.error import InputError
from ally.container.ioc import injected
from ally.container.support import setup
from ally.internationalization import _
from ally.support.sqlalchemy.util_service import deleteModel
from sql_alchemy.impl.entity import EntityGetServiceAlchemy, \
    EntityQueryServiceAlchemy, EntitySupportAlchemy
from sqlalchemy.orm.exc import NoResultFound
import re
    
# --------------------------------------------------------------------

@injected
@setup(IAccessService, name='accessService')
class AccessServiceAlchemy(EntityGetServiceAlchemy, EntityQueryServiceAlchemy, IAccessService):
    '''
    Implementation for @see: IAccessService that provides the ACL access.
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, AccessMapped, QAccess, path=Path.path, method=Method.name)
    
    def getAll(self, q=None, **options):
        '''
        @see: IAccessService.getAll
        '''
        if q:
            assert isinstance(q, QAccess), 'Invalid query %s' % q
            if QAccess.path.equal in q: q.path.equal = q.path.equal.strip().strip('/')
            if QAccess.method.equal in q: q.method.equal = q.method.equal.strip().upper()
        return super().getAll(q=q, **options)
    
    def insert(self, access):
        '''
        @see: IAccessService.insert
        '''
        assert isinstance(access, Access), 'Invalid access %s' % access

        dbAccess = AccessMapped()
        items, dbAccess.pathId = self.pathId(access.Path)
        dbAccess.methodId = self.methodId(access.Method)
        
        for item in items:
            if item == '*':
                if not access.Types: raise InputError(_('Expected at least one type for first *', Access.Types))
                if len(access.Types) <= len(dbAccess.types):
                    raise InputError(_('Expected a type for * at position %(position)i'),
                                     Access.Types, position=len(dbAccess.types) + 1)
                accessToType = AccessToType()
                accessToType.typeId = self.typeId(access.Types[len(dbAccess.types)])
                accessToType.position = len(dbAccess.types) + 1
                dbAccess.types.append(accessToType)
        
        dbAccess.Id = generateId(access.Path, access.Method)
        dbAccess.ShadowOf = access.ShadowOf
        self.session().add(dbAccess)
        return dbAccess.Id
        
    def delete(self, accessId):
        '''
        @see: IAccessService.delete
        '''
        return deleteModel(AccessMapped, accessId)
    
    # ----------------------------------------------------------------
    
    def pathId(self, path):
        '''
        Provides the path id for the provided path.
        '''
        assert isinstance(path, str), 'Invalid path %s' % path
        
        path = path.strip().strip('/')
        items = path.split('/')
        try: pathId, = self.session().query(Path.id).filter(Path.path == path).one()
        except NoResultFound:
            aclPath = Path()
            aclPath.path = path
            
            for k, item in enumerate(items, 1):
                if item == '*':
                    if aclPath.priority is None: aclPath.priority = k
                elif not re.match('\w*$', item):
                    raise InputError(_('Invalid path item \'%(item)s\', expected only alpha numeric characters or *'),
                                     Access.Path, item=item)
            if aclPath.priority is None: aclPath.priority = 0
            
            self.session().add(aclPath)
            self.session().flush((aclPath,))
            pathId = aclPath.id
        
        return items, pathId
    
    def methodId(self, method):
        '''
        Provides the method id for the provided method.
        '''
        assert isinstance(method, str), 'Invalid method %s' % method
        
        method = method.strip().upper()
        try: methodId, = self.session().query(Method.id).filter(Method.name == method).one()
        except NoResultFound:
            aclMethod = Method()
            aclMethod.name = method
            self.session().add(aclMethod)
            self.session().flush((aclMethod,))
            methodId = aclMethod.id
        return methodId
    
    def typeId(self, name):
        '''
        Provides the type id for the provided type name.
        '''
        assert isinstance(name, str), 'Invalid type name %s' % name
        
        name = name.strip()
        try: typeId, = self.session().query(Type.id).filter(Type.name == name).one()
        except NoResultFound:
            aclType = Type()
            aclType.name = name
            self.session().add(aclType)
            self.session().flush((aclType,))
            typeId = aclType.id
        return typeId
    
    # TODO: remove    
    def isDummy1Filter(self, id):
        print(id)
        return id == '00000000'
    
    # TODO: remove    
    def isDummy2Filter(self, id):
        print(id)
        return id == '2036D140'
