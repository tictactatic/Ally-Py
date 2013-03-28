'''
Created on Feb 7, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblage specification.
'''

import abc
import re

# --------------------------------------------------------------------

class Assemblage:
    '''
    Provides the assemblage data.
    '''
    __slots__ = ('id', 'types', 'hrefIdentifiers')
    
    def __init__(self, obj):
        '''
        Construct the assemblage based on the provided dictionary object.
        @see: assemblage/assemblage.api.assemblage
        
        @param obj: dictionary{string: string|list[string]}
            The dictionary used for defining the assemblage object, the object as is defined from response.
        '''
        assert isinstance(obj, dict), 'Invalid object %s' % obj
        
        self.id = obj['Id']
        assert isinstance(self.id, str), 'Invalid id %s' % self.id
        
        types = obj['Types']
        assert isinstance(types, list), 'Invalid types %s' % types
        if __debug__:
            for item in types: assert isinstance(item, str), 'Invalid type %s' % item
        self.types = set(item.lower() for item in types)
        
        self.hrefIdentifiers = obj['IdentifierList']['href']
        assert isinstance(self.hrefIdentifiers, str), 'Invalid identifiers reference %s' % self.hrefIdentifiers

class Identifier:
    '''
    Provides the assemblage identifier data.
    '''
    __slots__ = ('id', 'method', 'pattern', 'headersExclude', 'hrefMatchers')
    
    def __init__(self, obj):
        '''
        Construct the identifier based on the provided dictionary object.
        @see: assemblage/assemblage.api.assemblage
        
        @param obj: dictionary{string: string|list[string]}
            The dictionary used for defining the identifier object, the object as is defined from response.
        '''
        assert isinstance(obj, dict), 'Invalid object %s' % obj
        
        self.id = obj['Id']
        assert isinstance(self.id, str), 'Invalid id %s' % self.id
        
        method = obj['Method']
        assert isinstance(method, str), 'Invalid method %s' % method
        self.method = method.upper()
        
        pattern = obj['Pattern']
        assert isinstance(pattern, str), 'Invalid pattern %s' % pattern
        self.pattern = re.compile(pattern)
        
        headersExclude = obj.get('HeadersExclude')
        if headersExclude:
            if __debug__:
                assert isinstance(headersExclude, list), 'Invalid exclude headers %s' % headersExclude
                for item in headersExclude: assert isinstance(item, str), 'Invalid header pattern %s' % item
            self.headersExclude = [re.compile(item) for item in headersExclude]
        else: self.headersExclude = None
        
        self.hrefMatchers = obj['MatcherList']['href']
        assert isinstance(self.hrefMatchers, str), 'Invalid matchers reference %s' % self.hrefMatchers

class Matcher:
    '''
    Provides the identifier matcher data.
    '''
    __slots__ = ('name', 'namePrefix', 'pattern', 'reference', 'adjustPattern', 'adjustReplace')
    
    def __init__(self, obj):
        '''
        Construct the identifier matcher based on the provided dictionary object.
        @see: assemblage/assemblage.api.assemblage
        
        @param obj: dictionary{string: string|list[string]}
            The dictionary used for defining the identifier matcher object, the object as is defined from response.
        '''
        assert isinstance(obj, dict), 'Invalid object %s' % obj
        
        names = obj['Names']
        assert isinstance(names, list), 'Invalid names %s' % names
        if __debug__:
            assert names, 'At least one name is required'
            for item in names: assert isinstance(item, str), 'Invalid name %s' % item
        self.name = '.'.join(names)
        self.namePrefix = '%s.' % self.name

        pattern = obj['Pattern']
        assert isinstance(pattern, str), 'Invalid pattern %s' % pattern
        self.pattern = re.compile(pattern)
        
        reference = obj.get('Reference')
        if reference:
            assert isinstance(reference, str), 'Invalid reference %s' % reference
            self.reference = re.compile(reference)
        else: self.reference = None
        
        self.adjustPattern = obj.get('AdjustPattern')
        if __debug__ and self.adjustPattern:
            assert isinstance(self.adjustPattern, list), 'Invalid adjust patterns %s' % self.adjustPattern
            for item in self.adjustPattern: assert isinstance(item, str), 'Invalid adjust pattern %s' % item
            
        adjustReplace = obj.get('AdjustReplace')
        if __debug__:
            if adjustReplace:
                assert isinstance(adjustReplace, list), 'Invalid adjust replace %s' % adjustReplace
                assert len(self.adjustPattern) == len(adjustReplace), \
                'Required the same number of entries for patterns %s and replaces %s' % (self.adjustPattern, adjustReplace)
                for item in adjustReplace: assert isinstance(item, str), 'Invalid adjust replace %s' % item
                self.adjustReplace = [re.compile(item) for item in adjustReplace]
            else:
                assert not self.adjustPattern, 'Cannot have patterns %s without replaces' % self.adjustPattern
                self.adjustReplace = None

# --------------------------------------------------------------------

class IRepository(metaclass=abc.ABCMeta):
    '''
    The assemblage repository.
    '''
    
    @abc.abstractmethod
    def matchers(self, forType, method, uri, headers=None):
        '''
        Finds the matchers objects for the provided parameters.

        @param forType: string
            The mime type of the URI response to provide the matchers for.
        @param method: string
            The method to be matched for the matchers
        @param uri: string
            The URI that we need the matchers for.
        @param headers: dictionary{String, string}|None
            The headers to be matched for the identifier.
        @return: Iterable(Matcher)|None
            The found matchers, None if there is no matcher available.
        '''
