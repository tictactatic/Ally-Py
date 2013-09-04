'''
Created on Aug 6, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL access.
'''

from ..api.access import IAccessService, AccessCreate, generateId, QAccess, \
    generateHash
from ..meta.access import AccessMapped, EntryMapped, PropertyMapped
from ally.api.error import InputError
from ally.container.ioc import injected
from ally.container.support import setup
from ally.internationalization import _
from sql_alchemy.impl.entity import EntityGetServiceAlchemy, \
    EntityQueryServiceAlchemy, EntitySupportAlchemy
from sql_alchemy.support.util_service import deleteModel, iterateCollection, \
    insertModel
from ally.api.criteria import AsBoolean
    
# --------------------------------------------------------------------

@injected
@setup(IAccessService, name='accessService')
class AccessServiceAlchemy(EntityGetServiceAlchemy, EntityQueryServiceAlchemy, IAccessService):
    '''
    Implementation for @see: IAccessService that provides the ACL access.
    '''
    
    def __init__(self):
        EntitySupportAlchemy.__init__(self, AccessMapped, QAccess, isShadow=self.queryShadow)
    
    def getEntry(self, accessId, position):
        '''
        @see: IAccessService.getEntry
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(position, int), 'Invalid position %s' % position
        
        sql = self.session().query(EntryMapped)
        sql = sql.filter(EntryMapped.accessId == accessId).filter(EntryMapped.Position == position)
        return sql.one()
        
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
        
        sql = self.session().query(PropertyMapped)
        sql = sql.filter(PropertyMapped.accessId == accessId).filter(PropertyMapped.Name == name)
        return sql.one()
        
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
        assert isinstance(access, AccessCreate), 'Invalid access %s' % access

        dbAccess = insertModel(AccessMapped, access, Id=generateId(access.Path, access.Method), Hash=generateHash(access))
        assert isinstance(dbAccess, AccessMapped), 'Invalid mapped access %s' % dbAccess
        
        self.generateEntries(access, dbAccess.Id, dbAccess.Path.split('/'))
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
        assert isinstance(access, AccessCreate), 'Invalid access %s' % access
        
        if access.Shadowing or access.Shadowed:
            if access.Shadowing is None:
                raise InputError(_('Expected a shadowing if a shadowed is provided'), AccessCreate.Shadowed)
            if access.Shadowed is None:
                raise InputError(_('Expected a shadowed if a shadowing is provided'), AccessCreate.Shadowed)
            if access.Entries:
                raise InputError(_('No entries expected for shadows'), AccessCreate.Entries)
            assert isinstance(access.Shadowing, int), 'Invalid shadowing %s' % access.Shadowing
            assert isinstance(access.Shadowed, int), 'Invalid shadowed id %s' % access.Shadowed
            
            sql = self.session().query(EntryMapped).filter(EntryMapped.accessId == access.Shadowing)
            shadowingEntries = {entry.Position: entry.Signature for entry in sql.all()}
            
            sql = self.session().query(EntryMapped).filter(EntryMapped.accessId == access.Shadowed)
            shadowedEntries = {entry.Position: entry.Signature for entry in sql.all()}
            
            isShadow = True
        else: isShadow = False

        position = 1
        for item in items:
            if item != '*': continue
            entry = EntryMapped()
            entry.Position = position
            entry.accessId = accessId
            
            if isShadow:
                # Handling a shadow access.
                if access.EntriesShadowing:
                    assert isinstance(access.EntriesShadowing, dict), 'Invalid shadowing entries %s' % access.EntriesShadowing
                    sposition = access.EntriesShadowing.get(position)
                else: sposition = None
                if sposition is not None:
                    if sposition not in shadowingEntries:
                        raise InputError(_('Invalid shadowing position %(shadowing)i for position %(position)s'),
                                         AccessCreate.EntriesShadowing, shadowing=sposition, position=position)
                    signature = shadowingEntries.pop(sposition)
                    entry.Shadowing = sposition
                else:
                    if access.EntriesShadowed:
                        assert isinstance(access.EntriesShadowed, dict), 'Invalid shadowed entries %s' % access.EntriesShadowed
                        sposition = access.EntriesShadowed.get(position)
                    else: sposition = None
                    if sposition is None:
                        raise InputError(_('Cannot find shadowing or shadowed type for position %(position)s'))
                    if sposition not in shadowedEntries:
                        raise InputError(_('Invalid shadowed position %(shadowed)i for position %(position)s'),
                                         AccessCreate.EntriesShadowed, shadowed=sposition, position=position)
                    signature = shadowedEntries.pop(sposition)
                    entry.Shadowed = sposition
            
            else:
                # Handling a normal access.
                if not access.Entries: raise InputError(_('Expected at least one entry for first *'), AccessCreate.Entries)
                assert isinstance(access.Entries, dict), 'Invalid access entries %s' % access.Entries
                if position not in access.Entries:
                    raise InputError(_('Expected an entry for * at %(position)i'), AccessCreate.Entries, position=position)
                signature = access.Entries[position]
            
            entry.Signature = signature
            self.session().add(entry)
            position += 1

        if isShadow:
            if shadowingEntries:
                raise InputError(_('This shadowing lacks entries for shadow access at positions %(positions)s'),
                             AccessCreate.EntriesShadowing, positions=', '.join(shadowingEntries))
            if shadowedEntries:
                raise InputError(_('This shadowed lacks entries for shadow access at positions %(positions)s'),
                             AccessCreate.EntriesShadowed, positions=', '.join(shadowedEntries))
                
    def generateProperties(self, access, accessId):
        '''
        Generates the access properties.
        '''
        assert isinstance(access, AccessCreate), 'Invalid access %s' % access
        
        if not access.Properties: return
        assert isinstance(access.Properties, dict), 'Invalid access properties %s' % access.Properties
        for name, signature in access.Properties.items():
            prop = PropertyMapped()
            prop.Name = name
            prop.accessId = accessId
            prop.Signature = signature
            self.session().add(prop)

    def queryShadow(self, sql, crit):
        '''
        Processes the shadow query.
        '''
        assert isinstance(crit, AsBoolean), 'Invalid criteria %s' % crit
        if crit.value: return sql.filter(AccessMapped.Shadowing != None)
        return sql.filter(AccessMapped.Shadowing == None)
