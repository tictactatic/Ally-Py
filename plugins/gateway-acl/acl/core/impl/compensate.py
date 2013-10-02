'''
Created on Sep 2, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for handling ACL compensate access service.
'''

from acl.api.access import Access
from acl.core.spec import isCompatible, ICompensateProvider, \
    COMPENSATE_CREATE_MARKER
from acl.meta.access import EntryMapped, AccessMapped
from acl.meta.acl import WithAclAccess
from acl.meta.compensate import WithCompensate
from ally.api.error import IdError, InputError
from ally.internationalization import _
from ally.support.api.util_service import modelId
from sql_alchemy.support.mapper import MappedSupport
from sql_alchemy.support.util_service import SessionSupport
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import aliased

# --------------------------------------------------------------------

class CompensateServiceAlchemy(SessionSupport, ICompensateProvider):
    '''
    Provides support for handling the ACL compensate data. By ACL object is meant the object that has been configured to have the
    access mapping on it.
    '''
    
    def __init__(self, Acl, AclAccess, Compensate, signatures=None):
        '''
        Construct the compensate service alchemy.
        
        @param AclAccess: class of WithAclAccess
            The ACL access relation mapped class.
        @param Compensate: class of WithCompensate
            The compensate relation mapped class.
        @param signatures: dictionary{string: string|callable(identifier) -> string}
            A dictionary containing as keys the signatures that will be injected and as a value either the marker to be injected
            or a callable that takes the identifier as a parameter and provides the marker string value.
        '''
        assert isinstance(Acl, MappedSupport), 'Invalid mapped class %s' % Acl
        assert issubclass(AclAccess, WithAclAccess), 'Invalid acl access class %s' % AclAccess
        assert issubclass(Compensate, WithCompensate), 'Invalid compensate class %s' % Compensate
        if __debug__:
            if signatures is not None:
                assert isinstance(signatures, dict), 'Invalid fill in signatures %s' % signatures
                for signature, marker in signatures.items():
                    assert isinstance(signature, str), 'Invalid signature %s' % signature
                    assert isinstance(marker, str) or callable(marker), 'Invalid marker %s' % marker
        
        self.Acl = Acl
        self.AclIdentifier = modelId(Acl)
        self.AclAccess = AclAccess
        self.AliasAclAccess = aliased(AclAccess)
        self.Compensate = Compensate
        
        self.signatures = signatures
        
    def getCompensates(self, identifier, accessId):
        '''
        @see: ICompensatePrototype.getCompensates
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        
        sql = self.session().query(self.Compensate).join(self.AclAccess).join(self.Acl)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        return sql.enable_eagerloads(False).all()
    
    def addCompensate(self, identifier, accessId, compensatedId):
        '''
        @see: ICompensatePrototype.addCompensate
        '''
        assert isinstance(accessId, int), 'Invalid access id %s' % accessId
        assert isinstance(compensatedId, int), 'Invalid compensated access id %s' % compensatedId
        
        sql = self.session().query(AccessMapped, self.AclAccess.id).join(self.AclAccess).join(self.Acl)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        try: access, aclAccessId = sql.one()
        except NoResultFound: raise InputError(_('Access not allowed'))
        
        compensated = self.session().query(AccessMapped).get(compensatedId)
        if compensated is None: raise IdError(Access)
        assert isinstance(access, AccessMapped), 'Invalid access %s' % access
        assert isinstance(compensated, AccessMapped), 'Invalid access %s' % compensated
        
        if compensated.Method != access.Method: raise InputError(_('The compensated method is not compatible'), Access.Method)
        if compensated.Output != access.Output: raise InputError(_('The compensated output is not compatible'), Access.Output)
        
        sql = self.session().query(EntryMapped.Signature)
        sql = sql.filter(EntryMapped.accessId == accessId)
        sql = sql.order_by(EntryMapped.Position.desc())
        saccesses = [signature for signature, in sql.all()]
        
        sql = self.session().query(EntryMapped.Signature).filter(EntryMapped.accessId == compensatedId)
        sql = sql.order_by(EntryMapped.Position.desc())
        scompensateds = [signature for signature, in sql.all()]
        
        if len(saccesses) < len(scompensateds):
            raise InputError(_('To many compensated entries versus the access entries'))
        
        fixed = iter(reversed(access.Path.split('*')))
        items, mapping = [next(fixed)], {}
        for k, (saccess, scompensated) in enumerate(zip(saccesses, scompensateds)):
            if isCompatible(saccess, scompensated):
                items.append(COMPENSATE_CREATE_MARKER % (len(scompensateds) - k))
                items.append(next(fixed))
                mapping[len(saccesses) - k] = len(scompensateds) - k
            else:
                raise InputError(_('The compensated entry is not compatible with the access entry for position %(position)i'),
                                 position=len(scompensateds) - k)
        
        if len(saccesses) > len(scompensateds):
            if not self.signatures: raise InputError(_('Cannot provide a values for access prefix entries'))
            for k, saccess in enumerate(saccesses[len(scompensateds):]):
                for signature, marker in self.signatures.items():
                    if isCompatible(signature, saccess):
                        if isinstance(marker, str): items.append(marker)
                        else:
                            value = marker(identifier)
                            assert isinstance(value, str), 'Invalid maker %s return value \'%s\'' % (marker, value)
                            items.append(value)
                        items.append(next(fixed))
                        break
                else:
                    raise InputError(_('Cannot provide a value for access position %(position)i'),
                                     position=len(saccesses) - k)

        items.reverse()
        path = ''.join(items)

        sql = self.session().query(self.Compensate)
        sql = sql.filter(self.Compensate.aclAccessId == aclAccessId).filter(self.Compensate.Access == compensatedId)
        try: compensate = sql.one()
        except NoResultFound:
            compensate = self.Compensate()
            assert isinstance(compensate, WithCompensate), 'Invalid compensate %s' % compensate
            compensate.Access = compensatedId
            compensate.Path = path
            compensate.Mapping = mapping
            compensate.aclAccessId = aclAccessId
            self.session().add(compensate)
        else:
            compensate.Path = path
            compensate.Mapping = mapping
    
    def remCompensate(self, identifier, accessId, compensatedId):
        '''
        @see: ICompensatePrototype.remCompensate
        '''
        sql = self.session().query(self.Compensate).join(self.AclAccess)
        sql = sql.filter(self.AclAccess.accessId == accessId).filter(self.AclIdentifier == identifier)
        sql = sql.filter(self.Compensate.Access == compensatedId)
        try: compensate = sql.one()
        except NoResultFound: return False
        
        self.session().delete(compensate)
        return True

    # ----------------------------------------------------------------
    
    def iterateCompensates(self, acl):
        '''
        @see: ICompensateProvider.iterateCompensates
        '''
        sql = self.session().query(self.Compensate, self.AclAccess.accessId)
        sql = sql.join(self.AclAccess).join(self.Acl)
        sql = sql.filter(self.AclIdentifier.in_(acl))
        
        for compensate, accessId in sql.all():
            assert isinstance(compensate, WithCompensate), 'Invalid compensate %s' % compensate
            yield accessId, compensate, compensate.access
        
