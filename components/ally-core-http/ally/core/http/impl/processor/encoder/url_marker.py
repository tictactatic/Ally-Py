'''
Created on Apr 16, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides additional indexing markers.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed

# --------------------------------------------------------------------

NAME_HTTP_URL = 'URL'  # The marker name for HTTP URL.

GROUP_REFERENCE = 'reference'  # The group name for reference.

ACTION_CAPTURE = 'capture'  # The action name for capture.

# --------------------------------------------------------------------

class Mark(Context):
    '''
    The mark context.
    '''
    # ---------------------------------------------------------------- Defined
    group = definesIf(str, doc='''
    @rtype: string
    Indicates the mark group.
    ''')
    action = definesIf(str, doc='''
    @rtype: string
    Indicates the mark action.
    ''')
    
class Markers(Context):
    '''
    The indexing markers context.
    '''
    # ---------------------------------------------------------------- Defined
    markers = defines(dict, doc='''
    @rtype: dictionary{string: Marker}
    The registered markers.
    ''')
    
# --------------------------------------------------------------------

@injected
class URLMarkersHandler(HandlerProcessorProceed):
    '''
    Provides the basic support for registering markers.
    '''
        
    def process(self, markers:Markers, Marker:Context, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the general markers.
        '''
        assert isinstance(markers, Markers), 'Invalid markers %s' % markers
        assert issubclass(Marker, Mark), 'Invalid mark class %s' % Mark
        
        if markers.markers is None: markers.markers = {}
        else: assert NAME_HTTP_URL not in markers.markers, 'Already a marker for name \'%s\'' % NAME_HTTP_URL
        
        marker = markers.markers[NAME_HTTP_URL] = Marker()
        assert isinstance(marker, Mark), 'Invalid marker %s' % marker
        if Mark.group in marker: marker.group = GROUP_REFERENCE
        if Mark.action in marker: marker.action = ACTION_CAPTURE
