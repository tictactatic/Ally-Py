'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Specifications and general functions for ACL.
'''

from ally.api.operator.type import TypeProperty, TypeContainer
from ally.api.type import typeFor, Iter, Type
from binascii import crc32
from weakref import WeakKeyDictionary
import abc

# --------------------------------------------------------------------

COMPENSATE_CREATE_MARKER = '{%i}'
# The create marker string required to be used.

# --------------------------------------------------------------------

class IAclPermissionProvider(metaclass=abc.ABCMeta):
    '''
    Specification for ACL permission provider.
    '''
    
    @abc.abstractmethod
    def iteratePermissions(self, acl):
        '''
        Iterates all the ACL permissions for the provided acl.
        
        @param acl: object
            The acl resource(s) to iterate the permissions for.
        @return: Iterable(tuple(Access, dictionary{object: tuple(dictionary{integer:list[string]},
                                                                 dictionary{string:list[string]})}))
            Provides and iterator that yields tuples with the access and filters.
            The filters dictionary contains:
                identifier object: (filter paths for entries indexed by entry position,
                                    filter paths for properties indexed by property name)
        '''
        
class ICompensateProvider(metaclass=abc.ABCMeta):
    '''
    Specification for ACL compensate provider.
    '''
    
    @abc.abstractmethod
    def iterateCompensates(self, acl):
        '''
        Iterates all the ACL compensates for the provided acl.
        
        @param acl: object
            The acl resource(s) to iterate the compensates for.
        @return: Iterable(tuple(integer, Compensate, Access))
            The iterable providing tuples that have on the first position the compensating access id on the second the 
            compensate object and on the last position the compensated access. 
        '''
        
# --------------------------------------------------------------------

_signature_cache = WeakKeyDictionary()
def signature(obj):
    '''
    Provides the signature for the provided type.
    
    @param obj: Type or container for type container
        The type to provide the signature for.
    @return: string
        The signature.
    '''
    ftype = typeFor(obj)
    assert isinstance(ftype, Type), 'Invalid type %s' % ftype
    if ftype in _signature_cache: return _signature_cache[ftype]
    
    names, ctype, bname = [], ftype, '%s'
    
    if isinstance(ctype, Iter):
        assert isinstance(ctype, Iter)
        bname = '%s[%%s]' % ctype.__class__.__name__
        ctype = ctype.itemType
        
    if isinstance(ctype, (TypeProperty, TypeContainer)):
        isProperty, types = isinstance(ctype, TypeProperty), [ctype]
        while types:
            ctype = types.pop()
            if isProperty:
                assert isinstance(ctype, TypeProperty), 'Invalid property type %s' % ctype
                mtype = ctype.parent
                assert isinstance(mtype, TypeContainer), 'Invalid parent %s' % mtype
                names.append(bname % ('%s.%s.%s' % (mtype.clazz.__module__, mtype.clazz.__name__, ctype.name)))
                bases = ctype.parent.clazz.__bases__
            else:
                assert isinstance(ctype, TypeContainer), 'Invalid container type %s' % ctype
                names.append(bname % ('%s.%s' % (ctype.clazz.__module__, ctype.clazz.__name__)))
                bases = ctype.clazz.__bases__
                
            inherited = []
            for base in bases:
                mtype = typeFor(base)
                if not isinstance(mtype, TypeContainer): continue
                if isProperty:
                    assert isinstance(mtype, TypeContainer)
                    ptype = mtype.properties.get(ctype.name)
                    if not ptype: continue
                    assert isinstance(ptype, TypeProperty), 'Invalid property type %s' % ptype
                    if ctype.type == ptype.type: inherited.append(ptype)
                else: inherited.append(mtype)
                
            if inherited:
                inherited.reverse()
                types.extend(inherited)
                
    else: names.append(bname % ctype)
    
    signature = _signature_cache[ftype] = ''.join(('{0:0>8x}'.format(crc32(name.encode()))).upper() for name in names)
    return signature

def isCompatible(signature, withSignature):
    '''
    Checks if the signature is compatible with signature.
    
    @param signature: string
        The signature to check if compatible.
    @param withSignature: string
        The signature to check with.
    @return: boolean
        True if the signature is compatible, False otherwise.
    '''
    assert isinstance(signature, str), 'Invalid signature %s' % signature
    assert isinstance(withSignature, str), 'Invalid with signature %s' % withSignature
    
    if signature == withSignature: return True
    if not len(withSignature) > 8: return False
    
    if len(signature) > 8: signature = signature[:8]
        
    for k in range(0, len(withSignature), 8):
        if signature == withSignature[k:k + 8]: return True
    return False
