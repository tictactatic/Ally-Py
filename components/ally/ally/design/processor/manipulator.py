'''
Created on Mar 15, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides manipulator structure classes.
'''
from ally.design.processor.spec import IRepository, LIST_RESOLVER, IResolver
from ally.design.processor.repository import Repository, indexNames

# --------------------------------------------------------------------

class Mapping:
    '''
    Contains names mappings used for renaming.
    '''
    __slots__ = ('firstToSecond', 'secondToFirst')  # TODO: Gabriel: add more clear name and reduce filed after clearing the ideea
    
    def __init__(self):
        '''
        Constructs the mapping. 
        '''
        self.firstToSecond = {}
        self.secondToFirst = {}
        
    def map(self, first, second):
        '''
        Maps the first name to the second name.
        
        @param first: string
            The name to be mapped.
        @param second: string
            The name to be used instead of the first name.
        '''
        assert isinstance(first, str), 'Invalid first name %s' % first
        assert isinstance(second, str), 'Invalid second wrapper %s' % second
        
        namesSecond = self.firstToSecond.get(first)
        if namesSecond is None: namesSecond = self.firstToSecond[first] = []
        if second not in namesSecond: namesSecond.append(second)
        
        namesFirst = self.secondToFirst.get(second)
        if namesFirst is None: namesFirst = self.secondToFirst[second] = []
        if first not in namesFirst: namesFirst.append(first)
        
    def structure(self, repository):
        '''
        Structures the provided repository based on this mapping.
        
        @param repository: IRepository
            The repository to structure.
        @return: IRepository
            The restructured repository.
        '''
        assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
        
        resolvers = {}
        for second, resolver in repository.listContexts(LIST_RESOLVER).items():
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
            
            firsts = self.secondToFirst.get(second)
            if not firsts: continue
            assert isinstance(firsts, list), 'Invalid mapping %s' % firsts
            for first in firsts:
                current = resolvers.get(first)
                if current: resolver = resolver.solve(current)
                resolvers[first] = resolver
                    
        return Repository(resolvers)
    
    def restructure(self, repository, structured):
        '''
        Restructures back in the repository the structured repository.
        
        @param repository: IRepository
            The repository to restructure.
        @param structured: IRepository
            The repository to do the restructuring based on.
        '''
        assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
        assert isinstance(structured, IRepository), 'Invalid structured repository %s' % structured
        
        attributes = indexNames(structured.listAttributes())
        sresolvers = structured.listContexts(LIST_RESOLVER)
        resolvers = {}
        for second, attrs in indexNames(repository.listAttributes()).items():
            firsts = self.secondToFirst.get(second)
            
            if not firsts: continue
            assert isinstance(firsts, list), 'Invalid mapping %s' % firsts
            remaining = attributes.get(second)
            if not remaining: continue
            
            # TODO: Gabriel: Fix: Vezi ca populeaza si in reponse path, tre facut filtering
            for first in firsts:
                if not remaining: break
                resolver = sresolvers.get(first)
                resolver = resolver.copy(remaining.intersection(attrs))
                remaining.difference_update(resolver.list())
                
                current = resolvers.get(second)
                if current: resolver = resolvers.solve(current)
                resolvers[second] = resolver
                
        for second, remaining in attributes.items():
            firsts = self.secondToFirst.get(second)
            
            if not firsts: continue
            assert isinstance(firsts, list), 'Invalid mapping %s' % firsts
            
            # TODO: Gabriel: Fix: Vezi ca populeaza si in reponse path, tre facut filtering
            for first in firsts:
                if not remaining: break
                resolver = sresolvers.get(first)
                resolver = resolver.copy(remaining)
                remaining.difference_update(resolver.list())
                
                current = resolvers.get(second)
                if current: resolver = resolvers.solve(current)
                resolvers[second] = resolver
                
        repository.solve(Repository(resolvers))
