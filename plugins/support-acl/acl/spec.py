'''
Created on Jan 19, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ACL specifications.
'''

from ally.api.operator.type import TypeProperty
from ally.api.type import typeFor
from collections import Iterable
from itertools import chain
import abc

# --------------------------------------------------------------------

class Filter:
    '''
    The filter model contains data describes a filter to be used for a certain call or calls.
    '''
    
    def __init__(self, priority, authenticated, resource, filter):
        '''
        Construct the acl filter.
        
        @param priority: integer
            The priority of the filter, this is used whenever there are more then one filter in the same context in order to
            establish which one will be used.
        @param authenticated: TypeProperty
            The property type of the authenticated resource specific for the action taker.
        @param resource: TypeProperty
            The property type that is targeted for filtering.
        @param filter: object
            The filter is an object that can be used by the security services in order to filter the authenticated vs resource.
        '''
        assert isinstance(priority, int), 'Invalid priority %s' % priority
        authenticated = typeFor(authenticated)
        assert isinstance(authenticated, TypeProperty), 'Invalid property type %s' % authenticated
        resource = typeFor(resource)
        assert isinstance(resource, TypeProperty), 'Invalid property type %s' % resource
        
        self.priority = priority
        self.authenticated = authenticated
        self.resource = resource
        self.filter = filter

class RightBase(metaclass=abc.ABCMeta):
    '''
    The ACL right model base. Any class that extends the right base class needs to also override the "iterPermissions" class
    method.
    '''
    
    @classmethod
    def iterPermissions(cls, node, rights, method=None):
        '''
        Iterates over the permissions for the node with rights and optionally the method, the filters are joined base
        on the policy:
        - if a call has multiple representation and there is a filter for that call then only the call representation that
          can be filtered will be used and also the filter with the highest priority will be used.

        @param node: Node
            The node to get the permissions for.
        @param rights: Iterable(RightBase)|RightBase
            The rights to provide the permissions for.
        @param method: integer|None
            The method to get the permissions one of (GET, INSERT, UPDATE, DELETE) or a combination of those using the
            "|" operator, if None then all methods are considered.
        @return: Iterator(tuple(integer, Path, Invoker, dictionary{TypeProperty:Filter}))|
            The permissions tuples of (method, path, invoker, filters) for the provided node, rights and method.
            The filters will always have the resource types found in the path.
        '''
        if isinstance(rights, RightBase):
            clazz = type(rights)
            assert clazz.iterPermissions is not RightBase.iterPermissions, \
            'Invalid implementation %s, needs to override the \'iterPermissions\' class method' % clazz
            return clazz.iterPermissions(node, rights, method)
        assert isinstance(rights, Iterable), 'Invalid rights %s' % rights
        indexed = {}
        for right in rights:
            assert isinstance(right, RightBase), 'Invalid right %s' % right
            clazz = type(right)
            assert clazz.iterPermissions is not RightBase.iterPermissions, \
            'Invalid implementation %s, needs to override the \'iterPermissions\' class method' % clazz
            indexedRights = indexed.get(clazz)
            if indexedRights is None: indexedRights = indexed[clazz] = [right]
            else: indexedRights.append(right)
        permisions = []
        for clazz, rights in indexed.items(): permisions.extend(clazz.iterPermissions(node, rights, method))
        return permisions
    
    def __init__(self, name, description, type=None):
        '''
        Construct the right model.
        
        @param name: string
            The right name.
        @param description: string
            The description for the right.
        @param type: TypeAcl|None
            The type of the right.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(description, str), 'Invalid description %s' % description
        self.name = name.strip()
        self.description = description.strip()
        
        if type:
            assert isinstance(type, TypeAcl)
            type.add(self)
    
    @abc.abstractmethod
    def hasPermissions(self, node, method=None):
        '''
        Checks if there are any permissions for the provided node and optionally the method.

        @param node: Node
            The node to check the permissions for.
        @param method: integer|None
            The method to check for the filter, if None then all methods are considered.
        @return: boolean
            True if there are permissions for the provided node and method.
        '''

class TypeAcl:
    '''
    The ACL type model.
    '''
    
    def __init__(self, name, description, acl=None):
        '''
        Construct the type model.
        
        @param name: string
            The type name.
        @param description: string
            The description for the type.
        @param acl: Acl|None
            The acl of the type.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(description, str), 'Invalid description %s' % description
        self.name = name.strip()
        self.description = description.strip()
        self._rights = {}
        
        if acl:
            assert isinstance(acl, Acl)
            acl.add(self)
    
    def add(self, right):
        '''
        Add a new ACL right that is binded to this ACL type.
        
        @param right: RightBase
            The ACL right to be added.
        @return: Right
            The same right.
        '''
        assert isinstance(right, RightBase), 'Invalid right %s' % right
        assert right.name not in self._rights, 'Already a right with name %s' % right.name
        self._rights[right.name] = right
        return right
    
    def hasPermissions(self, node, method=None):
        '''
        Checks if there are any permissions for the provided node and optionally the method.

        @param node: Node
            The node to check the permissions for.
        @param method: integer|None
            The method to check for the filter, if None then all methods are considered.
        @return: boolean
            True if there are permissions for the provided node and method.
        '''
        for right in self._rights.values():
            assert isinstance(right, RightBase)
            if right.hasPermissions(node, method): return True
        return False
        
    def activeRights(self, node, method=None):
        '''
        Provides the rights that have valid accesses in respect with the provided node and optionally method.
        
        @param node: Node
            The node to provide the active rights for.
        @param method: integer|None
            The method to get the active rights for, if None then all methods are considered.
        @return: Iterable(RightBase)
            The iterable of active rights.
        '''
        for right in self._rights.values():
            assert isinstance(right, RightBase)
            if right.hasPermissions(node, method): yield right
            
    def activeRightsFor(self, node, *names, method=None):
        '''
        Provides the active rights based on the provided parameters.
        
        @param node: Node
            The node to provide the active types for.
        @param names: arguments[string|Iterable(string)]
            The right names to provide the rights for.
        @param method: integer|None
            The method to get the types rights for, if None then all methods are considered.
        @return: Iterable(RightBase)
            The active rights based on the provided data.
        '''
        if names:
            aclNames = namesOf(names)
            if not aclNames: return
        else: aclNames = None
        
        if aclNames is not None:
            for right in self.activeRights(node, method=method):
                assert isinstance(right, RightBase)
                if right.name in aclNames: yield right
        else:
            for right in self.activeRights(node, method=method): yield right

class Acl:
    '''
    The ACL repository.
    '''
    
    def __init__(self):
        '''
        Construct the ACL repository.
        '''
        self._types = {}
        
    def add(self, type):
        '''
        Add a new ACL type that is binded to this ACL repository.
        
        @param type: TypeAcl
            The ACL type to be added.
        @return: Type
            The same type.
        '''
        assert isinstance(type, TypeAcl), 'Invalid type %s' % type
        assert type.name not in self._types, 'Already a type with name %s' % type.name
        self._types[type.name] = type
        return type
    
    def activeTypes(self, node, method=None):
        '''
        Provides the types that have valid accesses in respect with the provided node and optionally method.
        
        @param node: Node
            The node to provide the active types for.
        @param method: integer|None
            The method to get the types rights for, if None then all methods are considered.
        @return: Iterable(TypeAcl)
            The iterable of active types.
        '''
        for type in self._types.values():
            assert isinstance(type, TypeAcl)
            if type.hasPermissions(node, method): yield type
            
    def activeRights(self, node, method=None):
        '''
        Provides the rights that have valid accesses in respect with the provided node and optionally method.
        
        @param node: Node
            The node to provide the active rights for.
        @param method: integer|None
            The method to get the active rights for, if None then all methods are considered.
        @return: Iterable(RightBase)
            The iterable of active rights.
        '''
        rights = []
        for typeAcl in self.activeTypes(node, method):
            assert isinstance(typeAcl, TypeAcl)
            rights.append(typeAcl.activeRights(node, method=method))
        return chain(*rights)
            
    def activeRightsFor(self, node, *names, method=None):
        '''
        Provides the active rights based on the provided parameters.
        
        @param node: Node
            The node to provide the active types for.
        @param names: arguments[string|Iterable(string)]
            The right names to provide the rights for.
        @param method: integer|None
            The method to get the types rights for, if None then all methods are considered.
        @return: Iterable(RightBase)
            The active rights based on the provided data.
        '''
        if names:
            aclNames = namesOf(names)
            if not aclNames: return ()
        else: aclNames = None
        
        if aclNames is not None:
            rights = []
            for typeAcl in self.activeTypes(node, method):
                assert isinstance(typeAcl, TypeAcl)
                rights.append(typeAcl.activeRightsFor(node, aclNames, method=method))
            return chain(*rights)
        
        return self.activeRights(node, method=method)

# --------------------------------------------------------------------

def namesOf(names):
    '''
    Compiles the names arguments into a single set of names.
    
    @param names: tuple(string|Iterable(string))
        The names to compile.
    @return: set(string)|None
        The set containing all the names, None if no names are specified.
    '''
    assert isinstance(names, tuple), 'Invalid names %s' % names
    if len(names) == 1 and isinstance(names[0], set): aclNames = names[0]
    else:
        aclNames = set()
        for name in names:
            if isinstance(name, str): aclNames.add(name)
            assert isinstance(name, Iterable), 'Invalid name %s' % name
            aclNames.update(name)
    return aclNames
