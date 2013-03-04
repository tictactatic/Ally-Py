'''
Created on Jun 28, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the URI request path handler.
'''

from ally.api.type import Scheme
from ally.container.ioc import injected
from ally.core.spec.resources import ConverterPath, Path, Converter, Normalizer, \
    Node
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.codes import PATH_FOUND, PATH_NOT_FOUND
from ally.http.spec.server import IEncoderPath
from ally.support.core.util_resources import findPath
from urllib.parse import quote, unquote
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    uri = requires(str)
    # ---------------------------------------------------------------- Optional
    argumentsOfType = optional(dict)
    # ---------------------------------------------------------------- Defined
    path = defines(Path, doc='''
    @rtype: Path
    The path to the resource node.
    ''')
    converterId = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for model id's.
    ''')
    normalizerParameters = defines(Normalizer, doc='''
    @rtype: Normalizer
    The normalizer to use for decoding parameters names.
    ''')
    converterParameters = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for the parameters values.
    ''')

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Optional
    encoderPath = optional(IEncoderPath, doc='''
    @rtype: IEncoderPath
    The path encoder used for encoding resource paths that will be rendered in the response.
    ''')
    # ---------------------------------------------------------------- Defined
    code = defines(str)
    status = defines(int)
    isSuccess = defines(bool)
    text = defines(str)
    converterId = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for model id's.
    ''')

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defined
    type = defines(str, doc='''
    @rtype: string
    The response content type.
    ''')

# --------------------------------------------------------------------

@injected
class URIHandler(HandlerProcessorProceed):
    '''
    Implementation for a processor that provides the searches based on the request URL the resource path, also
    populates the parameters and extension format on the request.
    '''

    resourcesRoot = Node
    # The resources node that will be used for finding the resource path.
    resourcesRootURI = None
    # The prefix to append to the resources Path encodings.
    converterPath = ConverterPath
    # The converter path used for handling the URL path.

    def __init__(self):
        assert isinstance(self.resourcesRoot, Node), 'Invalid resources node %s' % self.resourcesRoot
        assert self.resourcesRootURI is None or isinstance(self.resourcesRootURI, str), \
        'Invalid root URI %s' % self.resourcesRootURI
        assert isinstance(self.converterPath, ConverterPath), 'Invalid ConverterPath object %s' % self.converterPath
        super().__init__()

    def process(self, request:Request, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Process the URI to a resource path.
        '''
        assert isinstance(request, Request), 'Invalid required request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        assert isinstance(request.uri, str), 'Invalid request URI %s' % request.uri
        if response.isSuccess is False: return  # Skip in case the response is in error
        
        paths = request.uri.split('/')
        i = paths[-1].rfind('.') if len(paths) > 0 else -1
        if i < 0:
            extension = None
        else:
            extension = paths[-1][i + 1:].lower()
            paths[-1] = paths[-1][0:i]
        paths = [unquote(p) for p in paths if p]

        if extension: responseCnt.type = extension
        request.path = findPath(self.resourcesRoot, paths, self.converterPath)
        assert isinstance(request.path, Path), 'Invalid path %s' % request.path
        if not request.path.node:
            # we stop the chain processing
            response.code, response.status, response.isSuccess = PATH_NOT_FOUND
            assert log.debug('No resource found for URI %s', request.uri) or True
            return
        assert log.debug('Found resource for URI %s', request.uri) or True

        request.converterId = self.converterPath
        request.converterParameters = self.converterPath
        request.normalizerParameters = self.converterPath

        if Request.argumentsOfType in request and request.argumentsOfType is not None:
            request.argumentsOfType[Scheme] = request.scheme

        if Response.encoderPath in response and response.encoderPath:
            response.encoderPath = EncoderPathURI(response.encoderPath, self.converterPath, self.resourcesRootURI, extension)

        response.code, response.status, response.isSuccess = PATH_FOUND
        response.converterId = self.converterPath

# --------------------------------------------------------------------

class EncoderPathURI(IEncoderPath):
    '''
    Provides encoding for the URI paths generated by the URI processor.
    '''

    __slots__ = ('_wrapped', '_converterPath', '_rootURI', '_extension')

    def __init__(self, wrapped, converterPath, rootURI=None, extension=None):
        '''
        Construct the Path encoder.

        @param wrapped: IEncoderPath|None
            The wrapped encoder that provides string based path encodings.
        @param converterPath: ConverterPath
            The converter path to be used on Path objects to get the URI.
        @param rootURI: string|None
            The root URI to be considered for constructing a request path, basically the relative path root. None if the path
            is not relative.
        @param extension: string|None
            The extension to use on the encoded paths.
        '''
        assert isinstance(wrapped, IEncoderPath), 'Invalid wrapped encoder %s' % wrapped
        assert isinstance(converterPath, ConverterPath), 'Invalid converter path %s' % converterPath
        assert rootURI is None or isinstance(rootURI, str), 'Invalid root URI %s' % rootURI
        assert extension is None or isinstance(extension, str), 'Invalid extension %s' % extension
        
        self._wrapped = wrapped
        self._converterPath = converterPath
        self._rootURI = rootURI
        self._extension = extension

    def encode(self, path, parameters=None):
        '''
        @see: EncoderPath.encode
        '''
        if isinstance(path, Path):
            assert isinstance(path, Path)

            uri = []
            paths = path.toPaths(self._converterPath)
            uri.append('/'.join(paths))
            if self._extension:
                uri.append('.')
                uri.append(self._extension)
            elif path.node.isGroup:
                uri.append('/')
            elif paths[-1].count('.') > 0:
                uri.append('/')  # Added just in case the last entry has a dot in it and not to be consfused as a extension
            
            uri = quote(''.join(uri))
            if self._rootURI: uri = self._rootURI % uri
            
            return self._wrapped.encode(uri, parameters)
        return self._wrapped.encode(path, parameters)
