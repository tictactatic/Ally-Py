'''
Created on Mar 20, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for assemblage markers.
'''

from .domain_assemblage import modelAssemblage
from ally.api.config import model, service, call
from ally.api.type import Iter, Dict, List

# --------------------------------------------------------------------

@model(id='Id')
class MarkerPrototype:
    '''
    Provides the marker data used in assemblage.
        Id -            the id of the marker as it in found in indexes.
        Name -          unique name for the marker.
        Group -         the group of the marker.
        Action -        the action of the marker.
        Target -        the target of the marker.
        Values -        the list of values source of the marker, an entry value might contain place holders for prepared data,
                        an empty value marks a value that needs to be provided by the proxy server.
        Replace -       the regex pattern used for replace marker source content.
        ReplaceMapping -the content replace, as a key the value that needs to be replaced and as a value the replacing value.
                        if the replace provides a value that is not in this mapping then an empty string will be used.
        ReplaceValue -  the replace value for replace regex, this can contain group markers like \1,\2 .. identifying 
                        groups that are captured by replace regex.
    '''
    Id = int
    Name = str
    Group = str
    Action = str
    Target = str
    Replace = str
    ReplaceMapping = Dict(str, str)
    ReplaceValue = str
    Values = List(str)
    
@modelAssemblage(replace=MarkerPrototype)
class Marker(MarkerPrototype):
    '''
    Provides the marker data used in assemblage.
        Source -        the source for the marker.
    '''
    Source = MarkerPrototype

# --------------------------------------------------------------------

@service
class IAssemblageMarkerService:
    '''
    Provides the assemblage markers services.
    '''
    
    @call
    def getMarkers(self) -> Iter(Marker):
        '''
        Provides all assemblages markers.
        '''
    
