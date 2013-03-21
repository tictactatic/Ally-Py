'''
Created on Mar 20, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for assemblage data.
'''

from ally.api.config import model, service, call
from ally.api.type import Iter, List

# --------------------------------------------------------------------

@model
class Replacer:
    '''
    Provides the replace for assemblage injected content.
        Replacer -    contains the marked text used in the replaced content, this string can contain markers like
                      {1}, {2} ... identifying captured blocks from the matcher pattern, also can contain markers
                      like //1, //2 ... which represents blocks captured in the adjuster pattern.
    '''
    Replacer = str
    
@model
class Adjuster(Replacer):
    '''
    The adjuster for injected content.
        Pattern -    the regex pattern identifying what to be replaced with the Replacer in the content to be injected.
    '''
    Pattern = str

@model(id='Id')  
class Matcher:
    '''
    The matcher provides content specific patterns for an assemblage.
        Id -        unique identifier for the matcher.
        Types -     the types of the content that this matcher represents.
        Pattern -   the regex pattern used for identifying the assemblage in the main content.
        Reference - the regex pattern used for extracting the URI where content can be fetched for injecting, this regex
                    will be applied against the captured block from Pattern.
    '''
    Id = int
    Types = List(str)
    Pattern = str
    Reference = str

@model(id='Id')
class Assemblage:
    '''
    The assemblage provides the available names that can be injected in the main content.
        Id -        unique identifier for the assemblage.
        Name -      the name of the assemblage.
    '''
    Id = int
    Name = str

@model(id='Id')
class Identifier:
    '''
    Used for identifying URIs that have assemblages available.
        Id -        unique identifier for the identifier.
        Method -    the method name that this identifier applies for.
        Pattern -   the URI regex pattern to be matched.
    '''
    Id = int
    Method = str
    Pattern = str

# --------------------------------------------------------------------

@service
class IAssemblageService:
    '''
    Provides the assemblage services.
    '''
    
    @call
    def getIdentifiers(self) -> Iter(Identifier):
        '''
        Provides all identifiers.
        '''
    
    @call
    def getAssemblages(self, id: Identifier.Id) -> Iter(Assemblage):
        '''
        Provides all the assemblages that are available for the identifier.
        '''
    
    @call
    def getChildAssemblages(self, id: Assemblage.Id) -> Iter(Assemblage):
        '''
        Provides the child assemblages for the provided assemblage.
        '''
        
    @call
    def getMatchers(self, id: Assemblage.Id) -> Iter(Matcher):
        '''
        Provides the matchers for the assemblage.
        '''
    
    @call
    def getAdjusters(self, id: Matcher.Id) -> Iter(Adjuster):
        '''
        Provides the adjusters for the content to be injected.
        '''
    
    @call
    def getFailedReplacers(self, id: Matcher.Id) -> Iter(Replacer):
        '''
        Provides the replacers to be used when a request has failed and there is no content to be injected.
        '''
