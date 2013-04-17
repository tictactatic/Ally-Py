'''
Created on Apr 17, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the handler for setting the markers id's.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines, definesIf, \
    optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed

# --------------------------------------------------------------------

class Mark(Context):
    '''
    The mark context.
    '''
    # ---------------------------------------------------------------- Defined
    id = defines(int, doc='''
    @rtype: integer
    The mark id.
    ''')
    idSource = definesIf(int, doc='''
    @rtype: integer
    The mark source id.
    ''')
    # ---------------------------------------------------------------- Optional
    source = optional(str)
    
class Markers(Context):
    '''
    The indexing markers context.
    '''
    # ---------------------------------------------------------------- Required
    markers = requires(dict)
    
# --------------------------------------------------------------------

@injected
class ProvideMarkersIdHandler(HandlerProcessorProceed):
    '''
    Provides the basic support for registering markers.
    '''
    
    def __init__(self):
        super().__init__(Marker=Mark)
        
    def process(self, markers:Markers, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the markers id's.
        '''
        assert isinstance(markers, Markers), 'Invalid markers %s' % markers
        if not markers.markers: return  # No markers to provide id's for.
        assert isinstance(markers.markers, dict), 'Invalid markers %s' % markers.markers
        
        marks = list(markers.markers.items())
        marks.sort(key=lambda item: item[0])  # We order by name
        for id, (_name, marker) in enumerate(marks, 1):
            assert isinstance(marker, Mark), 'Invalid marker %s' % marker
            marker.id = id
        
        for marker in markers.markers.values():
            if Mark.source in marker and Mark.idSource in marker and marker.source is not None:
                assert marker.source in markers.markers, 'Invalid marker source %s' % marker.source
                source = markers.markers[marker.source]
                assert isinstance(source, Mark), 'Invalid marker %s' % source
                marker.idSource = source.id
