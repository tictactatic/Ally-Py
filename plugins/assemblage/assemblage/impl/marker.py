'''
Created on Mar 20, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for assemblage data.
'''

from ..api.marker import Marker, IAssemblageMarkerService
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain

# --------------------------------------------------------------------

class Mark(Context):
    '''
    The marker context.
    '''
    # ---------------------------------------------------------------- Required
    id = requires(int)
    group = requires(str)
    action = requires(str)
    target = requires(str)
    value = requires(str)
    idSource = requires(int)
    
class Markers(Context):
    '''
    The indexing markers context.
    '''
    # ---------------------------------------------------------------- Required
    markers = requires(dict)

# --------------------------------------------------------------------

@injected
@setup(IAssemblageMarkerService, name='assemblageMarkerService')
class AssemblageMarkerService(IAssemblageMarkerService):
    '''
    Implementation for @see: IAssemblageMarkerService.
    '''
    
    assemblyMarkers = Assembly; wire.entity('assemblyMarkers')
    # The markers processors to be used for fetching the markers.
    
    def __init__(self):
        assert isinstance(self.assemblyMarkers, Assembly), 'Invalid markers assembly %s' % self.assemblyMarkers
        
        self._processingMarkers = self.assemblyMarkers.create(markers=Markers, Marker=Mark)
    
    def getMarkers(self):
        '''
        @see: IAssemblageMarkerService.getMarkers
        '''
        proc = self._processingMarkers
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        chain = Chain(proc)
        chain.process(**proc.fillIn()).doAll()
        assert isinstance(chain.arg.markers, Markers), 'Invalid markers %s' % chain.arg.markers
        assert isinstance(chain.arg.markers.markers, dict), 'Invalid markers %s' % chain.arg.markers.markers
        
        markers = [self.asMarker(*item) for item in chain.arg.markers.markers.items()]
        markers.sort(key=lambda marker: marker.Id)
        return markers
    
    # ----------------------------------------------------------------
    
    def asMarker(self, name, mark):
        '''
        Creates a marker API object based on the provided mark context.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(mark, Mark), 'Invalid mark %s' % mark
        
        marker = Marker()
        marker.Id = mark.id
        marker.Name = name
        marker.Group = mark.group
        marker.Action = mark.action
        marker.Target = mark.target
        marker.Value = mark.value
        marker.Source = mark.idSource
        
        return marker
