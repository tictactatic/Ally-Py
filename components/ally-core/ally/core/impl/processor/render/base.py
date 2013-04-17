'''
Created on Jan 25, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the text base encoder processor handler.
'''

from ally.container.ioc import injected
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, \
    HandlerProcessorProceed
from ally.support.util_io import IInputStream
from collections import Callable
import abc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

NAME_BLOCK = 'block'  # The marker name for block.
NAME_ADJUST = 'adjust'  # The marker name for adjust.

GROUP_BLOCK = 'block'  # The group name for block.
GROUP_PREPARE = 'prepare'  # The group name for prepare.
GROUP_ADJUST = 'adjust'  # The group name for adjust.

ACTION_INJECT = 'inject'  # The action name for inject.
ACTION_CAPTURE = 'capture'  # The action name for capture.

# --------------------------------------------------------------------

class Mark(Context):
    '''
    The mark context.
    '''
    # ---------------------------------------------------------------- Defined
    hasValue = defines(bool, doc='''
    @rtype: boolean
    Flag indicating that a value is expected for the marker.
    ''')
    group = definesIf(str, doc='''
    @rtype: string
    Indicates the mark group.
    ''')
    action = definesIf(str, doc='''
    @rtype: string
    Indicates the mark action.
    ''')
    source = definesIf(str, doc='''
    @rtype: string
    Indicates the mark name that should be used as the content source for this mark.
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
class MarkersBaseHandler(HandlerProcessorProceed):
    '''
    Provides the basic support for registering markers.
    '''
    
    def __init__(self, Marker=Mark):
        super().__init__(Marker=Marker)
        
    def process(self, markers:Markers, Marker:Context, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the general markers.
        '''
        assert isinstance(markers, Markers), 'Invalid markers %s' % markers
        assert issubclass(Marker, Mark), 'Invalid mark class %s' % Mark
        
        markers = self.create(Marker)
        if markers.markers is None: markers.markers = markers
        else:
            for name in markers: assert name not in markers.markers, 'Already a marker for name \'%s\'' % name
            markers.markers.update(markers)
        
    # ----------------------------------------------------------------
    
    @abc.abstractmethod
    def create(self, Marker):
        '''
        Create the markers.
        
        @param Marker: ContextMetaClass
            The marker class to be used for the marker instances.
        @return: dictionary{string: Marker}
            The created markers.
        '''

@injected
class GeneralMarkersHandler(MarkersBaseHandler):
    '''
    Provides the the general markers.
    '''
        
    def create(self, Marker):
        '''
        @see: MarkersBaseHandler.create
        '''
        markers = {}
        
        marker = markers[NAME_BLOCK] = Marker(hasValue=True)
        assert isinstance(marker, Mark), 'Invalid marker %s' % marker
        if Mark.group in marker: marker.group = GROUP_BLOCK
        
        marker = markers[NAME_ADJUST] = Marker()
        if Mark.group in marker: marker.group = GROUP_ADJUST
        if Mark.action in marker: marker.action = ACTION_INJECT
        
        return markers

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    renderFactory = defines(Callable, doc='''
    @rtype: callable(Content, markers=None) -> IRender
    The renderer factory to be used for the response content, it receives as the first argument the content to render in
    and as the second argument is an optional one and provides the markers to be used in the rendering indexing, if not
    provided then no indexing will occur. 
    ''')
    
class Content(Context):
    '''
    The content context.
    '''
    # ---------------------------------------------------------------- Defined
    source = defines(IInputStream)
    length = defines(int)
    indexes = defines(list, doc='''
    @rtype: list[tuple(integer, tuple(string, string|None)|None)]
    The indexes table, basically a list of tuples that have on the first position the start index, on the second 
    position none if is an end index or another tuple that contains in the first position the marker name of the index,
    on the second an optional value.
    ''')
    # ---------------------------------------------------------------- Required
    charSet = requires(str)

class ResponseContent(Content):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(str)

# --------------------------------------------------------------------

@injected
class RenderBaseHandler(HandlerProcessor):
    '''
    Provides the text base renderer.
    '''

    contentTypes = dict
    # The dictionary{string:string} containing as a key the content types specific for this encoder and as a value
    # the content type to set on the response, if None will use the key for the content type response.

    def __init__(self):
        assert isinstance(self.contentTypes, dict), 'Invalid content types %s' % self.contentTypes
        super().__init__()

    def process(self, chain, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the renderer factory
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt

        # Check if the response is for this encoder
        if responseCnt.type not in self.contentTypes:
            assert log.debug('The content type \'%s\' is not for this %s encoder', responseCnt.type, self) or True
        else:
            contentType = self.contentTypes[responseCnt.type]
            if contentType:
                assert log.debug('Normalized content type \'%s\' to \'%s\'', responseCnt.type, contentType) or True
                responseCnt.type = contentType

            response.renderFactory = self.renderFactory
            return  # We need to stop the chain if we have been able to provide the encoding
        chain.proceed()

    # ----------------------------------------------------------------

    @abc.abstractclassmethod
    def renderFactory(self, content):
        '''
        Factory method used for creating a renderer for the provided content.
        
        @param content: Content
            The content to render in.
        @return: IRender
            The renderer for the content.
        '''
