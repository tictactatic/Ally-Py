'''
Created on Apr 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the generic marker provider.
'''

from ally.design.processor.context import Context
from ally.design.processor.attribute import definesIf, defines
from ally.container.ioc import injected
from ally.design.processor.handler import HandlerProcessorProceed

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
    target = definesIf(str, doc='''
    @rtype: string
    Indicates the mark target.
    ''')
    values = definesIf(list, doc='''
    @rtype: list[string]
    Indicates the values that should be used as the content source for this mark.
    ''')
    source = definesIf(str, doc='''
    @rtype: string
    Indicates the mark name that should be used as the content source for this mark.
    ''')
    replace = definesIf(str, doc='''
    @rtype: string
    The regex pattern used for replace marker source content.
    ''')
    replaceMapping = definesIf(dict, doc='''
    @rtype: dictionary{string: string}
    The content replace, as a key the value that needs to be replaced and as a value the replacing value.
    If the replace provides a value that is not in this mapping then an empty string will be used.
    ''')
    replaceValue = definesIf(str, doc='''
    @rtype: string
    The replace value for replace regex, this can contain group markers like \1,\2 .. identifying groups that
    are captured by replace.
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
class MarkersProviderHandler(HandlerProcessorProceed):
    '''
    Provides the markers provider based on a dictionary containing markers definitions.
    '''
    
    definitions = dict
    # The definitions dictionary containing the markers.
    # The dictionary has as a key the marker name and as a value another dictionary that contains as keys the marker property
    # and as a value the marker property value.
    
    def __init__(self, Marker=Mark):
        assert isinstance(self.definitions, dict), 'Invalid definitions %s' % self.definitions
        assert self.definitions, 'At least one definition is required'
        if __debug__:
            for name, definition in self.definitions.items():
                assert isinstance(name, str), 'Invalid definition name %s' % name
                assert isinstance(definition, dict), 'Invalid definition %s' % definition
                for name in definition: assert isinstance(name, str), 'Invalid definition property name %s' % name
        super().__init__(Marker=Marker)
        
    def process(self, markers:Markers, Marker:Context, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the general markers.
        '''
        assert isinstance(markers, Markers), 'Invalid markers %s' % markers
        assert issubclass(Marker, Mark), 'Invalid mark class %s' % Mark
        
        if markers.markers is None: markers.markers = {}
        for name, definition in self.definitions.items():
            assert name not in markers.markers, 'Already a marker for name %s' % name
            assert isinstance(definition, dict), 'Invalid definition %s' % definition
            
            marker = markers.markers[name] = Marker()
            for name, value in definition.items():
                if getattr(Mark, name) in marker: setattr(marker, name, value)
