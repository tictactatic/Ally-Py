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
    __slots__ = ('id', 'types', 'hrefIdentifiers', 'adjusters', 'errors')
    
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

        adjustPattern, adjustReplace = obj['AdjustPattern'], obj['AdjustReplace']
        if __debug__:
            assert isinstance(adjustPattern, list), 'Invalid adjust patterns %s' % adjustPattern
            assert isinstance(adjustReplace, list), 'Invalid adjust replace %s' % adjustReplace
            assert len(adjustPattern) == len(adjustReplace), \
            'Required the same number of entries for patterns %s and replaces %s' % (adjustPattern, adjustReplace)
            for item in adjustPattern: assert isinstance(item, str), 'Invalid adjust pattern %s' % item
            for item in adjustReplace: assert isinstance(item, str), 'Invalid adjust replace %s' % item
        self.adjusters = [(re.compile(replace), pattern) for replace, pattern in zip(adjustReplace, adjustPattern)]
        
        errorPattern, errorReplace = obj['ErrorPattern'], obj['ErrorReplace']
        if __debug__:
            assert isinstance(errorPattern, dict), 'Invalid error patterns %s' % errorPattern
            assert isinstance(errorReplace, dict), 'Invalid error replace %s' % errorReplace
            assert len(errorPattern) == len(errorReplace), \
            'Required the same number of entries for patterns %s and replaces %s' % (errorPattern, errorReplace)
            for key, value in errorPattern.items():
                assert isinstance(key, str), 'Invalid error pattern key %s' % key
                assert isinstance(value, str), 'Invalid error pattern value %s' % value
                assert isinstance(errorReplace.get(key), str), \
                'Invalid error replace value %s for key %s' % (errorReplace.get(key), key)
        self.errors = {key: (re.compile(replace), errorPattern.get(key)) for key, replace in errorReplace.items()}
        
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
    __slots__ = ('name', 'namePrefix', 'present', 'pattern', 'reference')
    
    def __init__(self, obj):
        '''
        Construct the identifier matcher based on the provided dictionary object.
        @see: assemblage/assemblage.api.assemblage
        
        @param obj: dictionary{string: string|list[string]}
            The dictionary used for defining the identifier matcher object, the object as is defined from response.
        '''
        assert isinstance(obj, dict), 'Invalid object %s' % obj
        
        self.name = obj.get('Name')
        if self.name:
            assert isinstance(self.name, str), 'Invalid name %s' % self.name
            self.namePrefix = '%s.' % self.name
        
        present = obj.get('Present')
        if present:
            assert isinstance(present, list), 'Invalid present names %s' % present
            if __debug__:
                for item in present: assert isinstance(item, str), 'Invalid present name %s' % item
            self.present = set(present)
        else: self.present = None

        pattern = obj['Pattern']
        assert isinstance(pattern, str), 'Invalid pattern %s' % pattern
        self.pattern = re.compile(pattern)
        
        reference = obj.get('Reference')
        if reference:
            assert isinstance(reference, str), 'Invalid reference %s' % reference
            self.reference = re.compile(reference)
        else: self.reference = None

# --------------------------------------------------------------------

class IRepository(metaclass=abc.ABCMeta):
    '''
    The assemblage repository.
    '''
    
    @abc.abstractmethod
    def assemblage(self, forType):
        '''
        Finds the matchers objects for the provided parameters.

        @param forType: string
            The mime type of the URI response to provide the matchers for.
        @return: Assemblage|None
            The found assemblage, None if there is no assemblage available for type.
        '''
    
    @abc.abstractmethod
    def matchers(self, assemblage, method, uri, headers=None):
        '''
        Finds the matchers objects for the provided parameters.

        @param assemblage: Assemblage
            The assemblage to provide the matchers for.
        @param method: string
            The method to be matched for the matchers
        @param uri: string
            The URI that we need the matchers for.
        @param headers: dictionary{String, string}|None
            The headers to be matched for the identifier.
        @return: Iterable(Matcher)|None
            The found matchers, None if there are no matchers available.
        '''
