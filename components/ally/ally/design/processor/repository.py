'''
Created on Mar 13, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides repository implementations.
'''

from .spec import IRepository, ResolverError, ContextMetaClass, IResolver, \
    LIST_RESOLVER, IAttribute
from collections import Iterable

# --------------------------------------------------------------------

class Repository(IRepository):
    '''
    Context resolvers repository.
    '''
    __slots__ = ('resolvers',)
    
    def __init__(self, resolvers=None):
        '''
        Construct the repository.
        
        @param contexts: dictionary{string: IResolver|ContextMetaClass}
            The contexts resolvers to construct the repository based on.
        '''
        self.resolvers = {}
        if resolvers:
            assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
            assert resolvers, 'No resolvers provided'
            for name, resolver in resolvers.items():
                assert isinstance(name, str), 'Invalid resolver name %s' % name
                if name in self.resolvers: raise ResolverError('There is already a context resolver for \'%s\'' % name)
                
                if isinstance(resolver, ContextMetaClass): resolver = resolverFor(resolver)
                assert isinstance(resolver, IResolver), 'Invalid context resolver %s' % resolver
                
                self.resolvers[name] = resolver
    
    def merge(self, other):
        '''
        @see: IRepository.merge
        '''
        if not isinstance(other, IRepository): other = Repository(other)
        assert isinstance(other, IRepository), 'Invalid other repository %s' % other
        
        for name, resolver in other.listContexts(LIST_RESOLVER).items():
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver 
            ownResolver = self.resolvers.get(name)
            if ownResolver is None: self.resolvers[name] = resolver
            else:
                assert isinstance(ownResolver, IResolver), 'Invalid resolver %s' % ownResolver 
                self.resolvers[name] = ownResolver.merge(resolver)
                
    def solve(self, other):
        '''
        @see: IRepository.solve
        '''
        if not isinstance(other, IRepository): other = Repository(other)
        assert isinstance(other, IRepository), 'Invalid other repository %s' % other
        
        for name, resolver in other.listContexts(LIST_RESOLVER).items():
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver 
            ownResolver = self.resolvers.get(name)
            if ownResolver is None: self.resolvers[name] = resolver
            else:
                assert isinstance(ownResolver, IResolver), 'Invalid resolver %s' % ownResolver 
                self.resolvers[name] = ownResolver.solve(resolver)
    
    def copy(self, names=None):
        '''
        @see: IRepository.copy
        '''
        if names is None:
            resolvers = dict(self.resolvers)
            
        else:
            resolvers = {}
            for name, attributes in indexNames(names).items():
                resolver = self.resolvers.get(name)
                if resolver:
                    assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
                    if attributes: resolvers[name] = resolver.copy(attributes)
                    else: resolvers[name] = resolver
        
        return Repository(resolvers)
    
    def extract(self, names):
        '''
        @see: IRepository.extract
        '''
        resolvers = {}
        for name, attributes in indexNames(names).items():
            resolver = self.resolvers.pop(name, None)
            if resolver:
                assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
                if attributes:
                    copy = resolvers[name] = resolver.copy(attributes)
                    assert isinstance(copy, IResolver), 'Invalid resolver %s' % copy
                    remaining = set(resolver.iterate())
                    remaining.difference_update(copy.iterate())
                    if remaining: self.resolvers[name] = resolver.copy(remaining)
                else:
                    resolvers[name] = resolver
        
        return Repository(resolvers)
    
    def listContexts(self, *flags):
        '''
        @see: IRepository.listContexts
        '''
        flags, contexts = set(flags), {}
        for name in self.resolvers: contexts[name] = None
        
        try: flags.remove(LIST_RESOLVER)
        except KeyError: pass
        else:
            for name in contexts: contexts[name] = self.resolvers[name]
            
        assert not flags, 'Unknown flags: %s' % ', '.join(flags)
        return contexts
    
    def listAttributes(self, *flags):
        '''
        @see: IRepository.listAttributes
        '''
        attributes = {}
        for nameCtx, resolver in self.resolvers.items():
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
            for nameAttr, value in resolver.list(*flags).items(): attributes[(nameCtx, nameAttr)] = value
        return attributes
            
    def create(self, *flags):
        '''
        @see: IRepository.create
        '''
        return {name: resolver.create(*flags) for name, resolver in self.resolvers.items()}

class RepositoryUsed(IRepository):
    '''
    Implementation for @see: IRepository, that only lists or creates the attributes that have been merged or solved, basically
    only the attributes that had an interaction. It uses a wrapped repository for the actual functionality.
    '''
    __slots__ = ('repository', 'used')
    
    def __init__(self, repository, used=None):
        '''
        Construct the repository with used tracking.
        
        @param repository: IRepository
            The repository to wrap.
        @param used: dictionary{string: set(string)}|None
            The used context names and as a value the used attributes.
        '''
        assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
        if used is not None:
            assert isinstance(used, dict), 'Invalid used %s' % used
            self.used = used
        else: self.used = {}
        self.repository = repository
        
    def merge(self, other):
        '''
        @see: IRepository.merge
        '''
        if not isinstance(other, IRepository): other = Repository(other)
        assert isinstance(other, IRepository), 'Invalid other repository %s' % other
        indexNames(other.listAttributes(), self.used)
        self.repository.merge(other)
            
    def solve(self, other):
        '''
        @see: IRepository.solve
        '''
        if not isinstance(other, IRepository): other = Repository(other)
        assert isinstance(other, IRepository), 'Invalid other repository %s' % other
        indexNames(other.listAttributes(), self.used)
        self.repository.solve(other)
        
    def copy(self, names=None):
        '''
        @see: IRepository.copy
        ''' 
        return RepositoryUsed(self.repository.copy(names), self.used)
    
    def extract(self, names):
        '''
        @see: IRepository.extract
        '''
        return RepositoryUsed(self.repository.extract(names), self.used)
    
    def listContexts(self, *flags):
        '''
        @see: IRepository.listContexts
        '''
        listing = {}
        for name, value in self.repository.listContexts(*flags).items():
            used = self.used.get(name)
            if used:
                if isinstance(value, IResolver):
                    assert isinstance(value, IResolver)
                    value = value.copy(used)
                listing[name] = value
        return listing
        
    def listAttributes(self, *flags):
        '''
        @see: IRepository.listAttributes
        '''
        listing = {}
        for name, value in self.repository.listAttributes(*flags).items():
            nameCtx, nameAttr = name
            if nameAttr in self.used.get(nameCtx, ()): listing[name] = value
        return listing
        
    def create(self, *flags):
        '''
        @see: IRepository.create
        '''
        if not self.used: return {}
        names = [(nameCtx, nameAttr) for nameCtx, used in self.used.items() for nameAttr in used]
        return self.repository.copy(names).create(*flags)
        
# --------------------------------------------------------------------
    
def resolverFor(clazz):
    '''
    Provides the resolver for the provided context class.
    
    @param clazz: ContextMetaClass
        The context class to get the resolver for.
    '''
    assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
    theClass = None
    for attribute in clazz.__attributes__.values():
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        resolverClass = attribute.resolver()
        assert issubclass(resolverClass, IResolver), 'Invalid resolver class %s' % resolverClass
        if theClass is None: theClass = resolverClass
        elif issubclass(theClass, resolverClass): theClass = resolverClass
        else:
            assert issubclass(resolverClass, theClass), \
            'Incompatible resolver classes %s with %s in %s' % (theClass, resolverClass, clazz)
    assert theClass is not None, 'No resolver class could be obtained for %s' % clazz
    return theClass(clazz)

def indexNames(names, indexed=None):
    '''
    Indexes the names based on context and attribute name.
    
    @param names: Iterable(string|tuple(string, string))
        The context or attribute names to index.
    @param indexed: dictionary{string: set(string)|None}|None
        The indexed names dictionary to update, if not provided one will be created.
    @return: dictionary{string: set(string)|None}
        The indexed names, as a key the context name and as a value the context attributes or None if
        no attributes names are provided.
    '''
    assert isinstance(names, Iterable), 'Invalid names %s' % names
    if indexed is None: indexed = {}
    assert isinstance(indexed, dict), 'Invalid indexed %s' % indexed

    for name in names:
        if isinstance(name, tuple):
            nameCtx, nameAttr = name
            assert isinstance(nameCtx, str), 'Invalid context name %s' % nameCtx
            assert isinstance(nameAttr, str), 'Invalid attribute name %s' % nameAttr
            indexedAttrs = indexed.get(nameCtx)
            if indexedAttrs is None: indexedAttrs = indexed[nameCtx] = set()
            indexedAttrs.add(nameAttr)
        else:
            assert isinstance(name, str), 'Invalid name %s' % name
            if name not in indexed: indexed[name] = None
            
    return indexed
