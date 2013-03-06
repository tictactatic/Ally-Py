'''
Created on Mar 6, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the path encoder that can handle the resources path.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.impl.node import NodeProperty
from ally.core.spec.resources import ConverterPath, Path
from ally.design.processor.attribute import defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IEncoderPath
from urllib.parse import quote
import logging
import re

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    extension = optional(str)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    encoderPath = defines(IEncoderPath, doc='''
    @rtype: IEncoderPath
    The path encoder used for encoding resource paths that will be rendered in the response.
    ''')

# --------------------------------------------------------------------

@injected
class ResourcePathEncoderHandler(HandlerProcessorProceed):
    '''
    Implementation for a processor that provides the resource path encoding.
    '''

    resourcesRootURI = None
    # The prefix to append to the resources Path encodings.
    converterPath = ConverterPath
    # The converter path used for handling the URL path.

    def __init__(self):
        assert self.resourcesRootURI is None or isinstance(self.resourcesRootURI, str), \
        'Invalid root URI %s' % self.resourcesRootURI
        assert isinstance(self.converterPath, ConverterPath), 'Invalid ConverterPath object %s' % self.converterPath
        super().__init__()
        
        if self.resourcesRootURI:
            parts = self.resourcesRootURI.split('%s')
            parts = (re.escape(part) for part in parts)
            self.resourcesRootPattern = '%s'.join(parts)
        else:
            self.resourcesRootPattern = None

    def process(self, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Process the resource path encoder.
        '''
        assert isinstance(request, Request), 'Invalid required request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        if Request.extension in request: extension = request.extension
        else: extension = None
        
        if response.encoderPath is None: response.encoderPath = EncoderPathResource(self, extension)
        else: response.encoderPath = EncoderPathResource(self, extension, response.encoderPath)

# --------------------------------------------------------------------

class EncoderPathResource(IEncoderPath):
    '''
    Provides encoding for the resource paths.
    '''
    __slots__ = ('handler', 'wrapped', 'extension')

    def __init__(self, handler, extension=None, wrapped=None):
        '''
        Construct the resource Path encoder.

        @param handler: ResourcePathEncoderHandler
            The handler containing the configurations for resource path encoder.
        @param extension: string|None
            The extension to use on the encoded paths.
        @param wrapped: IEncoderPath|None
            The wrapped encoder that provides string based path encodings.
        '''
        assert isinstance(handler, ResourcePathEncoderHandler), 'Invalid handler %s' % handler
        assert extension is None or isinstance(extension, str), 'Invalid extension %s' % extension
        assert wrapped is None or isinstance(wrapped, IEncoderPath), 'Invalid wrapped encoder %s' % wrapped
        
        self.handler = handler
        self.wrapped = wrapped
        self.extension = extension

    def encode(self, path, invalid=None, **keyargs):
        '''
        @see: EncoderPath.encode
        
        @param invalid: @see: Path.toPaths
            The callable to handle invalid matches.
        
        @keyword asPattern: boolean
            Flag indicating that the encoded path is used as a pattern.
        @keyword asQuoted: boolean
            Flag indicating that the encoded path should be quoted. 
        '''
        asPattern, asQuoted = keyargs.get('asPattern', False), keyargs.get('asQuoted', True)
        assert isinstance(asPattern, bool), 'Invalid as pattern flag %s' % asPattern
        assert isinstance(asQuoted, bool), 'Invalid as quoted flag %s' % asQuoted
        if isinstance(path, Path):
            assert isinstance(path, Path)
            
            uri, paths = [], path.toPaths(self.handler.converterPath, invalid=invalid)
            
            if asPattern: uri.append('\\/'.join(paths))
            else: uri.append('/'.join(paths))
            if self.extension:
                if asPattern: uri.append('\\.')
                else: uri.append('.')
                uri.append(self.extension)
            elif not asPattern:
                if path.node.isGroup: uri.append('/')
                elif paths[-1].count('.') > 0:
                    # Added just in case the last entry has a dot in it and not to be confused as a extension
                    uri.append('/')  
            
            uri = ''.join(uri)
            if asPattern:
                if self.handler.resourcesRootPattern: uri = self.handler.resourcesRootPattern % uri
            else:
                if asQuoted: uri = quote(uri)
                if self.handler.resourcesRootURI: uri = self.handler.resourcesRootURI % uri
            
            if self.wrapped: return self.wrapped.encode(uri, **keyargs)
            return uri
        
        elif self.wrapped is None:
            assert asPattern is False, 'Cannot encode as pattern the provided path %s' % path
            assert invalid is not None, 'Cannot invalid replacer expected %s' % invalid
            assert not keyargs, 'Invalid key arguments %s' % keyargs
            return path
        
        if asPattern: return self.wrapped.encode(path, **keyargs)
        return self.wrapped.encode(path, **keyargs)
