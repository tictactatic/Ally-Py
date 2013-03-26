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

@model(id='Id')
class Assemblage:
    '''
    Provides the response assemblage.
        Id -        unique identifier for the assemblage.
        Types -     the types of the content that this assemblage represents.
    '''
    Id = str
    Types = List(str)

@model(id='Id')
class Structure:
    '''
    Provides the assemblage structure and if available information related to identifying the
    URI associated with the structure.
        Id -            unique identifier for the structure.
        Method -        the method name that this identifier applies for, if no method is provided then the structure
                        does not apply to an URI.
        Pattern -       the URI regex pattern to be matched, if no pattern is provided then the structure
                        does not apply to an URI.
    '''
    Id = int
    Method = str
    Pattern = str

@model(id='Name')
class Matcher:
    '''
    Provides the available names that can be injected in the main content.
        Id -            unique identifier for the matcher within structure.
        Name -          the name of the matcher, if not present it means that this is an intermediate matcher.
        Types -         the types of the content that this matcher represents.
        Pattern -       the regex pattern used for identifying the assemblage in the main content.
        Reference -     the regex pattern used for extracting the URI where content can be fetched for injecting, this regex
                        will be applied against the captured block from Pattern.
        Collateral -    collateral subordinated structure for this matcher.
        AdjustPattern - the regex pattern identifying what to be replaced with the AdjustReplace in the content to be injected.
        AdjustReplace - contains the marked text used in the replaced content, this string can contain markers like
                        {1}, {2} ... identifying captured blocks from the matcher pattern, also can contain markers
                        like //1, //2 ... which represents blocks captured in the adjuster pattern.
    '''
    Name = str
    Pattern = str
    Reference = str
    Collateral = Structure
    AdjustPattern = List(str)
    AdjustReplace = List(str)

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
    def getStructure(self, assemblageId: Assemblage, structureId:Structure) -> Structure:
        '''
        Provides the structure.
        '''
         
    @call
    def getStructures(self, assemblageId: Assemblage) -> Iter(Structure.Id):
        '''
        Provides all structure that are available for the assemblage.
        '''
        
    @call
    def getMatchers(self, assemblageId: Assemblage, structureId:Structure) -> Iter(Matcher):
        '''
        Provides all matchers that are available for the structure.
        '''
    
