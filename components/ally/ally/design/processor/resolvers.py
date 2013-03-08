'''
Created on Mar 8, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the resolvers implementations.
'''

from .spec import ContextMetaClass, IAttribute, ResolverError, IResolver, \
    IResolvers
from collections import Iterable
from itertools import chain

# --------------------------------------------------------------------

class ResolversBase(IResolvers):
    '''
    Base implementation for a @see: IResolvers for basic functionality.
    '''
    __slots__ = ('_resolvers', '_locked')
    
    def __init__(self):
        '''
        Construct the base resolver.
        '''
        self._resolvers = {}
        self._locked = False
        
    def lock(self):
        '''
        @see: IResolvers.lock
        '''
        self._locked = True
        
    # ----------------------------------------------------------------
    
    def iterateNames(self):
        '''
        @see: IResolvers.iterateNames
        '''
        return self._resolvers.keys()
    
    def iterate(self):
        '''
        @see: IResolvers.iterate
        '''
        return self._resolvers.items()
    
    # ----------------------------------------------------------------
    
    def validateLock(self):
        '''
        Validates the lock.
        '''
        if self._locked: raise ResolverError('Resolvers are locked')
    
    def getResolver(self, key):
        '''
        Provides the resolver for the key.
        
        @param key: tuple(string, string)
            The key to get the resolver for.
        @return: IResolver|None
            The resolver.
        '''
        assert isinstance(key, tuple), 'Invalid key %s' % key
        assert len(key) == 2, 'Invalid key %s' % (key,)
        assert isinstance(key[0], str), 'Invalid first key entry %s' % (key,)
        assert isinstance(key[1], str), 'Invalid last key entry %s' % (key,)
        
        return self._resolvers.get(key)
        
    def addResolver(self, key, resolver):
        '''
        Adds the resolver for the key.
        
        @param key: tuple(string, string)
            The key to add the resolve for.
        @param resolver: IResolver
            The resolver to add.
        '''
        assert isinstance(key, tuple), 'Invalid key %s' % key
        assert len(key) == 2, 'Invalid key %s' % (key,)
        assert isinstance(key[0], str), 'Invalid first key entry %s' % (key,)
        assert isinstance(key[1], str), 'Invalid last key entry %s' % (key,)
        assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
        self.validateLock()
        
        self._resolvers[key] = resolver
        
    def popResolver(self, key):
        '''
        Pops the resolver for the key.
        
        @param key: tuple(string, string)
            The key to get the resolver for.
        @return: IResolver
            The resolver.
        '''
        assert isinstance(key, tuple), 'Invalid key %s' % key
        assert len(key) == 2, 'Invalid key %s' % (key,)
        assert isinstance(key[0], str), 'Invalid first key entry %s' % (key,)
        assert isinstance(key[1], str), 'Invalid last key entry %s' % (key,)
        self.validateLock()
        
        return self._resolvers.pop(key)
    
    def __str__(self):
        s, grouped = [], {}
        for key in self.iterateNames():
            names = grouped.get(key[0])
            if names is None: names = grouped[key[0]] = []
            names.append(key[1])
        for nameCtx in sorted(grouped.keys()):
            s.append('\t%s:' % nameCtx)
            s.append('\t\t%s' % ', '.join(sorted(grouped[nameCtx])))
        
        if not s: return '%s empty' % self.__class__.__name__
        return '%s:\n%s' % (self.__class__.__name__, '\n'.join(s))

# --------------------------------------------------------------------

class Resolvers(ResolversBase):
    '''
    Attributes resolvers repository.
    '''
    __slots__ = ()
    
    def __init__(self, locked=False, contexts=None):
        '''
        Construct the resolvers attributes repository.

        @param locked: boolean
            If True then the resolvers cannot be modified.
        @param contexts: dictionary{string, ContextMetaClass)|None
            The contexts to have the resolvers created based on.
        '''
        assert isinstance(locked, bool), 'Invalid locked flag %s' % locked
        super().__init__()
        
        if contexts is not None:
            assert isinstance(contexts, dict), 'Invalid contexts %s' % contexts
            for name, context in contexts.items():
                assert isinstance(name, str), 'Invalid context name %s' % name
                assert isinstance(context, ContextMetaClass), 'Invalid context class %s' % context
        
                for attribute in context.__attributes__.values():
                    assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
                    attribute.push(name, self)
                    
        if locked: self.lock()
        
    def add(self, name, attribute, resolver):
        '''
        @see: IResolvers.add
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(attribute, str), 'Invalid attribute %s' % attribute
        assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
        
        self.addResolver((name, attribute), resolver)
                    
    def merge(self, other, joined=True):
        '''
        @see: IResolvers.merge
        '''
        if not isinstance(other, IResolvers): other = Resolvers(True, other)
        assert isinstance(other, IResolvers), 'Invalid other resolvers %s' % other
        assert isinstance(joined, bool), 'Invalid joined flag %s' % joined
    
        for key, resolver in other.iterate():
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
            assert isinstance(key, tuple), 'Invalid key %s' % key
    
            resolv = self.getResolver(key)
            if resolv is None:
                if joined: resolver.push(key[0], self)
            else:
                assert isinstance(resolv, IResolver), 'Invalid resolver %s' % resolv 
                resolv.merge(resolver).push(key[0], self)
                
    def solve(self, other, joined=True):
        '''
        @see: IResolvers.solve
        '''
        if not isinstance(other, IResolvers): other = Resolvers(True, other)
        assert isinstance(other, IResolvers), 'Invalid other resolvers %s' % other
        assert isinstance(joined, bool), 'Invalid joined flag %s' % joined
    
        for key, resolver in other.iterate():
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
            assert isinstance(key, tuple), 'Invalid key %s' % key
            
            resolv = self.getResolver(key)
            if resolv is None:
                if joined: resolver.push(key[0], self)
            else:
                resolver.solve(resolv).push(key[0], self)
    
    def copy(self, names=None):
        '''
        @see: IResolvers.copy
        '''
        copy = Resolvers()
        if names:
            assert isinstance(names, Iterable), 'Invalid names %s' % names
            for name in names:
                if isinstance(name, tuple):
                    resolver = self.getResolver(name)
                    if resolver:
                        assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
                        resolver.push(name[0], copy)
                else:
                    assert isinstance(name, str), 'Invalid context or attribute name %s' % name
                    for key, resolver in self.iterate():
                        assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
                        if key[0] == name: resolver.push(name, copy)
        else:
            for key, resolver in self.iterate():
                assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
                resolver.push(key[0], copy)
            
        return copy
    
    def extract(self, names):
        '''
        @see: IResolvers.extract
        '''
        assert isinstance(names, Iterable), 'Invalid names %s' % names
        
        toExtract = []
        for name in names:
            if isinstance(name, tuple):
                if name in self.iterateNames(): toExtract.append(name)
            else:
                assert isinstance(name, str), 'Invalid context or attribute name %s' % name
                for key in self.iterateNames():
                    if key[0] == name: toExtract.append(key)
                
        extracted = Resolvers()
        for key in toExtract:
            resolver = self.popResolver(key)
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
            resolver.push(key[0], extracted)
        
        return extracted

    def validate(self):
        '''
        @see: IResolvers.validate
        '''
        for key, resolver in self.iterate():
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
            if not resolver.isAvailable(): raise ResolverError('The \'%s.%s\' is not available for %s' % (key + (resolver,)))

class ResolversFilter(Resolvers):
    '''
    Attributes resolvers repository that filters based on context names and delegates them to a contained repository.
    '''
    __slots__ = ('_filtered', '_routingHere', '_routingThere', '_deactivated')
    
    def __init__(self, filtered, routing):
        '''
        Construct the filtered resolvers attributes repository.
        @see: Resolvers.__init__

        @param filtered: ResolversBase
            If filtered repository.
        @param routing: dictionary{string: string}
            Routing dictionary, as a key the context name as it is known in this resolvers repository and as value the
            actual name from the filtered repository (they can be the same if the context have the same name).
        '''
        assert isinstance(filtered, ResolversBase), 'Invalid filtered resolvers %s' % filtered
        assert isinstance(routing, dict), 'Invalid routing %s' % routing
        reversed = {}
        for name, value in routing.items():
            assert isinstance(name, str), 'Invalid name %s' % name
            assert isinstance(value, str), 'Invalid name %s' % value
            reversed[value] = name
        assert len(routing) == len(reversed), 'Invalid routing %s, need to have unique values' % routing
        super().__init__()
        
        self._filtered = filtered
        self._routingHere = reversed
        self._routingThere = routing
        self._deactivated = False
                
    def iterateNames(self):
        '''
        @see: IResolvers.iterateNames
        '''
        if self._deactivated: return super().iterateNames()
        filtered = []
        for key in self._filtered.iterateNames():
            rname = self._routingThere.get(key[0])
            if rname is not None: filtered.append((rname, key[1]))
        return chain(super().iterateNames(), filtered)
    
    def iterate(self):
        '''
        @see: IResolvers.iterate
        '''
        if self._deactivated: return super().iterate()
        filtered = []
        for key, resolver in self._filtered.iterate():
            rname = self._routingThere.get(key[0])
            if rname is not None: filtered.append(((rname, key[1]), resolver))
        return chain(super().iterate(), filtered)
    
    # ----------------------------------------------------------------
    
    def solveInFiltered(self):
        '''
        Solves the rest of unfiltered resolvers (the ones that are not routed by filtering), 
        '''
        self._deactivated = True
        self._filtered.solve(self)
        self._deactivated = False
        
    # ----------------------------------------------------------------
    
    def validateLock(self):
        '''
        Validates lock and deactivated.
        '''
        if self._deactivated: raise ResolverError('Resolvers filter are deactivated, no modifications allowed')
        super().validateLock()
        
    def getResolver(self, key):
        '''
        @see: ResolversBase.getResolver
        '''
        assert isinstance(key, tuple), 'Invalid key %s' % key
        assert len(key) == 2, 'Invalid key %s' % (key,)
        assert isinstance(key[0], str), 'Invalid first key entry %s' % (key,)
        assert isinstance(key[1], str), 'Invalid last key entry %s' % (key,)
        
        rname = self._routingHere.get(key[0])
        if rname is not None: return self._filtered.getResolver((rname, key[1]))
        return super().getResolver(key)
        
    def addResolver(self, key, resolver):
        '''
        @see: ResolversBase.addResolver
        '''
        assert isinstance(key, tuple), 'Invalid key %s' % key
        assert len(key) == 2, 'Invalid key %s' % (key,)
        assert isinstance(key[0], str), 'Invalid first key entry %s' % (key,)
        assert isinstance(key[1], str), 'Invalid last key entry %s' % (key,)
        self.validateLock()
        
        rname = self._routingHere.get(key[0])
        if rname is not None: self._filtered.addResolver((rname, key[1]), resolver)
        else: super().addResolver(key, resolver)
        
    def popResolver(self, key):
        '''
        @see: ResolversBase.popResolver
        '''
        assert isinstance(key, tuple), 'Invalid key %s' % key
        assert len(key) == 2, 'Invalid key %s' % (key,)
        assert isinstance(key[0], str), 'Invalid first key entry %s' % (key,)
        assert isinstance(key[1], str), 'Invalid last key entry %s' % (key,)
        self.validateLock()
        
        rname = self._routingHere.get(key[0])
        if rname is not None: return self._filtered.popResolver((rname, key[1]))
        return super().popResolver(key)
