'''
Created on Feb 7, 2013

@package: gateway service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the gateway specification.
'''

import abc

# --------------------------------------------------------------------

class IRepository(metaclass=abc.ABCMeta):
    '''
    The gateways repository.
    '''
    
    @abc.abstractmethod
    def find(self, method=None, headers=None, uri=None, error=None):
        '''
        Finds the gateway object filtered by the provided parameters.

        @param method: string|None
            The method to be matched for the gateway.
        @param headers: dictionary{String, string}|None
            The headers to be matched for the gateway.
        @param uri: string|None
            The URI that needs to match the gateway patterns.
        @param error: integer|None
            The error to be matched for the gateway. If an error is provided then only the matchings that resolve errors will
            be returned.
        @return: Match|None
            The found match, None if there is no gateway to respect the provided parameters.
        '''
    
    @abc.abstractmethod
    def allowsFor(self, headers=None, uri=None):
        '''
        Provides the allowed methods for the provided parameters.
        
        @param headers: dictionary{String, string}|None
            The headers to be matched for the gateway.
        @param uri: string|None
            The URI that needs to match the gateway patterns.
        @return: set(string)
            The list of allowed methods.
        '''
    
    @abc.abstractmethod
    def obtainCache(self, identifier):
        '''
        Obtains the cache dictionary for the provided identifier.
        
        @param identifier: object
            The identifier used for identifying the cache.
        @return: dictionary{...}
            The cache dictionary, if none available for the identifier then one will be created.
        '''
        
# --------------------------------------------------------------------

class RepositoryJoined(IRepository):
    '''
    Repository that uses other repositories to provide services.
    '''
    __slots__ = ('_repositories',)
    
    def __init__(self, main, *repositories):
        '''
        Construct the joined repositories.
        
        @param main: IRepository
            The main repository, this will be used for storing caches.
        @param repositories: arguments[IRepository]
            The repositories to join with the main repositories.
        '''
        assert isinstance(main, IRepository), 'Invalid main repository %s' % main
        assert repositories, 'At least one other repository is required for joining'
        if __debug__:
            for repository in repositories: assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
        
        self._repositories = [main]
        self._repositories.extend(repositories)
        
    def find(self, method=None, headers=None, uri=None, error=None):
        '''
        @see: IRepository.find
        '''
        for repository in self._repositories:
            assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
            match = repository.find(method, headers, uri, error)
            if match is not None: return match
        
    def allowsFor(self, headers=None, uri=None):
        '''
        @see: IRepository.allowsFor
        '''
        allowed = set()
        for repository in self._repositories:
            assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
            allowed.update(repository.allowsFor(headers, uri))
        return allowed
        
    def obtainCache(self, identifier):
        '''
        @see: IRepository.obtainCache
        '''
        return self._repositories[0].obtainCache(identifier)
