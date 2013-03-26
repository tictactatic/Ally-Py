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
        
        self.types = obj['Types']
        assert isinstance(self.types, list), 'Invalid types %s' % self.types
        if __debug__:
            for item in self.types: assert isinstance(item, str), 'Invalid type %s' % item
        
        self.hrefIdentifiers = obj['IdentifierList']['href']
        assert isinstance(self.hrefIdentifiers, str), 'Invalid identifiers reference %s' % self.hrefIdentifiers

class Identifier:
    '''
    Provides the assemblage identifier data.
    '''
    __slots__ = ('method', 'pattern', 'hrefMatchers')
    
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
        
        self.hrefMatchers = obj['MatcherList']['href']
        assert isinstance(self.hrefMatchers, str), 'Invalid matchers reference %s' % self.hrefMatchers

class Matcher:
    '''
    Provides the identifier matcher data.
    '''
    __slots__ = ('name', 'pattern', 'reference', 'adjustPattern', 'adjustReplace')
    
    def __init__(self, obj):
        '''
        Construct the identifier matcher based on the provided dictionary object.
        @see: assemblage/assemblage.api.assemblage
        
        @param obj: dictionary{string: string|list[string]}
            The dictionary used for defining the identifier matcher object, the object as is defined from response.
        '''
        assert isinstance(obj, dict), 'Invalid object %s' % obj
        
        self.name = obj['Name']
        assert isinstance(self.name, list), 'Invalid name %s' % self.name
        if __debug__:
            for item in self.name: assert isinstance(item, str), 'Invalid name %s' % item
        
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
            
        self.adjustReplace = obj.get('AdjustReplace')
        if __debug__:
            if self.adjustReplace:
                assert isinstance(self.adjustReplace, list), 'Invalid adjust replace %s' % self.adjustReplace
                assert len(self.adjustPattern) == len(self.adjustReplace), \
                'Required the same number of entries for patterns %s and replaces %s' % (self.adjustPattern, self.adjustReplace)
                for item in self.adjustReplace: assert isinstance(item, str), 'Invalid adjust replace %s' % item
            else:
                assert not self.adjustPattern, 'Cannot have patterns %s without replaces' % self.adjustPattern

# --------------------------------------------------------------------

class IRepository(metaclass=abc.ABCMeta):
    '''
    The assemblage repository.
    '''
    
    @abc.abstractmethod
    def matchers(self, type, method, uri):
        '''
        Finds the matchers objects for the provided parameters.

        @param type: string
            The mime type of the URI response to provide the matchers for.
        @param method: string
            The method to be matched for the matchers
        @param uri: string
            The URI that we need the matchers for.
        @return: Iterable(Matcher)
            The found matchers.
        '''
