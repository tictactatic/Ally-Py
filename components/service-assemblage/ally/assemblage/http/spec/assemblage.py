'''
Created on Feb 7, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblage specification.
'''

import re
import abc

# --------------------------------------------------------------------

class Assemblage:
    '''
    Provides the assemblage data.
    '''
    __slots__ = ('id', 'method', 'pattern', 'matcherListHref')
    
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
        
        self.method = obj['Method']
        assert isinstance(self.method, str), 'Invalid method %s' % self.method
        
        pattern = obj['Pattern']
        assert isinstance(pattern, str), 'Invalid pattern %s' % pattern
        self.pattern = re.compile(pattern)
        
        self.matcherListHref = obj['MatcherList']['href']
        assert isinstance(self.matcherListHref, str), 'Invalid matcher list reference %s' % self.matcherListHref

class Matcher:
    '''
    Provides the assemblage matcher data.
    '''
    __slots__ = ('name', 'types', 'pattern', 'reference', 'adjustPattern', 'adjustReplace', 'matcherListHref')
    
    def __init__(self, obj):
        '''
        Construct the assemblage matcher based on the provided dictionary object.
        @see: assemblage/assemblage.api.assemblage
        
        @param obj: dictionary{string: string|list[string]}
            The dictionary used for defining the assemblage matcher object, the object as is defined from response.
        '''
        assert isinstance(obj, dict), 'Invalid object %s' % obj
        
        self.name = obj['Name']
        assert isinstance(self.name, str), 'Invalid name %s' % self.name
        
        types = obj.get('Types')
        if types:
            assert isinstance(types, list), 'Invalid types %s' % types
            if __debug__:
                for item in types: assert isinstance(item, str), 'Invalid type %s' % item
            self.types = set(types.lower() for item in types)
        else: self.types = None
        
        pattern = obj.get('Pattern')
        if pattern:
            assert isinstance(pattern, str), 'Invalid pattern %s' % pattern
            self.pattern = re.compile(pattern)
        else: self.pattern = None
        
        reference = obj.get('Reference')
        if reference:
            assert isinstance(reference, str), 'Invalid reference %s' % reference
            self.reference = re.compile(reference)
        else: self.reference = None
        
        self.adjustPattern = obj.get('AdjustPattern')
        if __debug__ and self.adjustPattern:
            assert isinstance(self.adjustPattern, list), 'Invalid adjust patterns %s' % self.adjustPattern
            for item in self.adjustPattern: assert isinstance(item, str), 'Invalid adjust pattern %s' % item
            
        self.adjustReplace = obj.get('AdjustReplace')
        if __debug__ and self.adjustReplace:
            assert isinstance(self.adjustReplace, list), 'Invalid adjust replace %s' % self.adjustReplace
            for item in self.adjustReplace: assert isinstance(item, str), 'Invalid adjust replace %s' % item
            
        self.matcherListHref = obj['MatcherList']['href']
        assert isinstance(self.matcherListHref, str), 'Invalid matcher list reference %s' % self.matcherListHref

# --------------------------------------------------------------------

class IRepository(metaclass=abc.ABCMeta):
    '''
    The assemblage repository.
    '''
    
    @abc.abstractmethod
    def matchers(self, method, uri, type):
        '''
        Finds the matchers objects for the provided parameters.

        @param method: string
            The method to be matched for the matchers
        @param uri: string
            The URI that we need the matchers for.
        @param type: string
            The mime type of the uri response to provide the matchers for.
        @return: dictionary{string: Matcher}
            The found matchers indexed by matcher name.
        '''
        
    @abc.abstractmethod
    def subMatchers(self, matcher):
        '''
        Provides the sub matchers objects for the provided matcher.

        @param matcher: Matcher
            The matcher to provide the sub matchers for.
        @return: dictionary{string: Matcher}
            The sub matchers indexed by matcher name.
        '''
