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

@model(id='Name')
class Matcher:
    '''
    Provides the available names that can be injected in the main content.
        Name -          the unique name of the matcher within assemblage.
        Types -         the types of the content that this matcher represents.
        Pattern -       the regex pattern used for identifying the assemblage in the main content.
        Reference -     the regex pattern used for extracting the URI where content can be fetched for injecting, this regex
                        will be applied against the captured block from Pattern.
        AdjustPattern - the regex pattern identifying what to be replaced with the AdjustReplace in the content to be injected.
        AdjustReplace - contains the marked text used in the replaced content, this string can contain markers like
                        {1}, {2} ... identifying captured blocks from the matcher pattern, also can contain markers
                        like //1, //2 ... which represents blocks captured in the adjuster pattern.
    '''
    Name = str
    Types = List(str)
    Pattern = str
    Reference = str
    AdjustPattern = List(str)
    AdjustReplace = List(str)

@model(id='Id')
class Assemblage:
    '''
    Used for identifying assemblage URIs that have assemblages available.
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
    def getAssemblages(self) -> Iter(Assemblage):
        '''
        Provides all assemblages.
        '''
    
    @call
    def getMatchers(self, id: Assemblage.Id, name:Matcher.Name=None) -> Iter(Matcher):
        '''
        Provides all child matchers that are available for the assemblage and optionally the matcher name.
        '''
    
