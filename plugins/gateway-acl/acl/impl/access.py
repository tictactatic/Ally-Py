'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL access.
'''

from ..api.access import IAccessService, Construct, generateId, QAccess
from ..meta.access import AccessMapped, EntryMapped, PropertyMapped
from ..meta.acl_intern import Path, Method, Type
from acl.api.access import generateHash
from ally.api.error import InputError
from ally.container.ioc import injected
from ally.container.support import setup
from ally.internationalization import _
from ally.support.sqlalchemy.util_service import deleteModel, iterateCollection
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
    
    def getEntry(self, accessId, position):
        '''
        @see: IAccessService.getEntry
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(position, int), 'Invalid position %s' % position
        
        sqlQuery = self.session().query(EntryMapped)
        sqlQuery = sqlQuery.filter(EntryMapped.accessId == accessId).filter(EntryMapped.Position == position)
        return sqlQuery.one()
        
    def getEntries(self, accessId):
        '''
        @see: IAccessService.getEntries
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        return iterateCollection(self.session().query(EntryMapped.Position).filter(EntryMapped.accessId == accessId))
    
    def getProperty(self, accessId, name):
        '''
        @see: IAccessService.getProperty
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(name, str), 'Invalid property name %s' % name
        
        sqlQuery = self.session().query(PropertyMapped)
        sqlQuery = sqlQuery.filter(PropertyMapped.accessId == accessId).filter(PropertyMapped.Name == name)
        return sqlQuery.one()
        
    def getProperties(self, accessId):
        '''
        @see: IAccessService.getProperties
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        return iterateCollection(self.session().query(PropertyMapped.Name).filter(PropertyMapped.accessId == accessId))
    
    def insert(self, access):
        '''
        @see: IAccessService.insert
        '''
        assert isinstance(access, Construct), 'Invalid access %s' % access

        dbAccess = AccessMapped()
        items, dbAccess.pathId = self.pathId(access.Path)
        dbAccess.methodId = self.methodId(access.Method)
        dbAccess.Id = generateId(access.Path, access.Method)
        dbAccess.Shadowing = access.Shadowing
        dbAccess.Shadowed = access.Shadowed
        dbAccess.Hash = generateHash(access)
        self.session().add(dbAccess)
        
        self.generateEntries(access, dbAccess.Id, items)
        self.generateProperties(access, dbAccess.Id)

        return access.Id
        
    def delete(self, accessId):
        '''
        @see: IAccessService.delete
        '''
        return deleteModel(AccessMapped, accessId)
    
    # ----------------------------------------------------------------
    
    def generateEntries(self, access, accessId, items):
        '''
        Generates the access entries.
        '''
        assert isinstance(access, Construct), 'Invalid access %s' % access
        
        if access.Shadowing or access.Shadowed:
            if access.Shadowing is None:
                raise InputError(_('Expected a shadowing if a shadowed is provided'), Construct.Shadowed)
            if access.Shadowed is None:
                raise InputError(_('Expected a shadowed if a shadowing is provided'), Construct.Shadowed)
            if access.Types:
                raise InputError(_('No types expected for shadows'), Construct.Types)
            assert isinstance(access.Shadowing, int), 'Invalid shadowing %s' % access.Shadowing
            assert isinstance(access.Shadowed, int), 'Invalid shadowed id %s' % access.Shadowed
            
            sqlQuery = self.session().query(EntryMapped).filter(EntryMapped.accessId == access.Shadowing)
            shadowingEntries = {entry.Position: entry.Type for entry in sqlQuery.all()}
            
            sqlQuery = self.session().query(EntryMapped).filter(EntryMapped.accessId == access.Shadowed)
            shadowedEntries = {entry.Position: entry.Type for entry in sqlQuery.all()}
            
            isShadow = True
        else: isShadow = False

        position = 1
        for item in items:
            if item == '*':
                entry = EntryMapped()
                entry.Position = position
                entry.accessId = accessId
                
                if isShadow:
                    # Handling a shadow access.
                    if access.TypesShadowing:
                        assert isinstance(access.TypesShadowing, dict), 'Invalid shadowing types %s' % access.TypesShadowing
                        sposition = access.TypesShadowing.get(position)
                    else: sposition = None
                    if sposition is not None:
                        if sposition not in shadowingEntries:
                            raise InputError(_('Invalid shadowing position %(shadowing)i for position %(position)s'),
                                             Construct.TypesShadowing, shadowing=sposition, position=position)
                        typeName = shadowingEntries.pop(sposition)
                        entry.Shadowing = sposition
                    else:
                        if access.TypesShadowed:
                            assert isinstance(access.TypesShadowed, dict), 'Invalid shadowed types %s' % access.TypesShadowed
                            sposition = access.TypesShadowed.get(position)
                        else: sposition = None
                        if sposition is None:
                            raise InputError(_('Cannot find shadowing or shadowed type for position %(position)s'))
                        if sposition not in shadowedEntries:
                            raise InputError(_('Invalid shadowed position %(shadowed)i for position %(position)s'),
                                             Construct.TypesShadowed, shadowed=sposition, position=position)
                        typeName = shadowedEntries.pop(sposition)
                        entry.Shadowed = sposition
                
                else:
                    # Handling a normal access.
                    if not access.Types: raise InputError(_('Expected at least one type for first *'), Construct.Types)
                    assert isinstance(access.Types, dict), 'Invalid access types %s' % access.Types
                    if position not in access.Types:
                        raise InputError(_('Expected a type for * at %(position)i'), Construct.Types, position=position)
                    typeName = access.Types[position]
                
                entry.typeId = self.typeId(typeName)
                self.session().add(entry)
                position += 1

        if isShadow:
            if shadowingEntries:
                raise InputError(_('This shadowing lacks types for shadow access at positions %(positions)s'),
                             Construct.TypesShadowing, positions=', '.join(shadowingEntries))
            if shadowedEntries:
                raise InputError(_('This shadowed lacks types for shadow access at positions %(positions)s'),
                             Construct.TypesShadowed, positions=', '.join(shadowedEntries))
                
    def generateProperties(self, access, accessId):
        '''
        Generates the access properties.
        '''
        assert isinstance(access, Construct), 'Invalid access %s' % access
        
        if not access.Properties: return
        assert isinstance(access.Properties, dict), 'Invalid access properties %s' % access.Properties
        for name, typeName in access.Properties.items():
            prop = PropertyMapped()
            prop.Name = name
            prop.accessId = accessId
            prop.typeId = self.typeId(typeName)
            self.session().add(prop)
    
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
                                     Construct.Path, item=item)
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
        print('1Filter:', id)
        return False
    
    # TODO: remove    
    def isDummy2Filter(self, id):
        print('2Filter:', id)
        return True
