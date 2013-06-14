'''
Created on Mar 6, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the path encoder that can handle invokers.
'''

from ally.api.operator.type import TypeProperty
from ally.container.ioc import injected
from ally.core.http.spec.server import IEncoderPathInvoker
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import defines, optional, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.server import IEncoderPath
from itertools import chain
from urllib.parse import quote
import re

# --------------------------------------------------------------------

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    hasMandatorySlash = requires(bool, doc='''
    @rtype: boolean
    Flag indicating that a trailing slash is mandatory for path.
    ''')
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Context, doc='''
    @rtype: Context
    The invoker node.
    ''')
    path = requires(list, doc='''
    @rtype: list[Context]
    The path elements.
    ''')
    isCollection = requires(bool, doc='''
    @rtype: boolean
    If True it means that the invoker provides a collection.
    ''')

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str, doc='''
    @rtype: string
    The element name.
    ''')
    property = requires(TypeProperty, doc='''
    @rtype: TypeProperty
    The property represented by the element.
    ''')

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Optional
    extension = optional(str)
    # ---------------------------------------------------------------- Required
    converterPath = requires(Converter)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    encoderPathInvoker = defines(IEncoderPathInvoker, doc='''
    @rtype: IEncoderInvoker
    The path encoder used for encoding invokers that will be rendered in the response.
    ''')
    # ---------------------------------------------------------------- Optional
    encoderPath = optional(IEncoderPath)

# --------------------------------------------------------------------

@injected
class InvokerPathEncoderHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the resource path encoding.
    '''

    resourcesRootURI = None
    # The prefix to append to the resources Path encodings.

    def __init__(self):
        assert self.resourcesRootURI is None or isinstance(self.resourcesRootURI, str), \
        'Invalid root URI %s' % self.resourcesRootURI
        super().__init__(Node=Node, Invoker=Invoker, Element=Element)
        
        if self.resourcesRootURI:
            parts = self.resourcesRootURI.split('%s')
            assert len(parts) == 2, 'Invalid resource root %s, has not marker' % self.resourcesRootURI
            prefix, suffix = parts
            prefix, suffix = prefix.rstrip('/'), suffix.lstrip('/')
            if prefix: self.patternPrefix = (re.escape(prefix),)
            else: self.patternPrefix = ()
            if suffix: self.patternSuffix = (re.escape(suffix),)
            else: self.patternSuffix = ()
        else:
            self.patternPrefix = self.patternSuffix = None

    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the invoker path encoder.
        '''
        assert isinstance(request, Request), 'Invalid required request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        if Request.extension in request: extension = request.extension
        else: extension = None
        
        response.encoderPathInvoker = EncoderPathInvoker(self, request.converterPath, response.encoderPath, extension)

# --------------------------------------------------------------------

class EncoderPathInvoker(IEncoderPathInvoker):
    '''
    Provides encoding for the resource paths.
    '''
    __slots__ = ('handler', 'converter', 'encoderPath', 'extension')

    def __init__(self, handler, converter, encoderPath, extension):
        '''
        Construct the resource Path encoder.

        @param handler: InvokerPathEncoderHandler
            The handler containing the configurations for resource path encoder.
        @param converter: Converter
            The converter to use for the path.
        @param encoderPath: IEncoderPath|None
            The encoder that provides string based path encodings.
        @param extension: string|None
            The extension to use on the encoded paths.
        '''
        assert isinstance(handler, InvokerPathEncoderHandler), 'Invalid handler %s' % handler
        assert isinstance(converter, Converter), 'Invalid converter %s' % converter
        assert extension is None or isinstance(extension, str), 'Invalid extension %s' % extension
        assert encoderPath is None or isinstance(encoderPath, IEncoderPath), 'Invalid path encoder %s' % encoderPath
        
        self.handler = handler
        self.converter = converter
        self.encoderPath = encoderPath
        self.extension = extension

    def encode(self, invoker, values=None, quoted=True):
        '''
        @see: IEncoderPathInvoker.encode
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert values is None or isinstance(values, dict), 'Invalid values %s' % values
        assert isinstance(quoted, bool), 'Invalid as quoted flag %s' % quoted
        assert invoker.path, 'No path available for invoker %s' % invoker
        
        path = []
        for el in invoker.path:
            assert isinstance(el, Element), 'Invalid element %s' % el
            if el.property:
                assert isinstance(el.property, TypeProperty), 'Invalid element property %s' % el.property
                assert isinstance(values, dict), 'Invalid values %s' % values
                
                value = values.get(el.property)
                if value is None:
                    # We try to see if there is a model object for property
                    value = values.get(el.property.parent)
                    if value is not None: value = getattr(value, el.property.name)
                
                assert value is not None, 'No value could be found for %s' % el.property
                if not isinstance(value, str): value = self.converter.asString(value, el.property)
                if quoted: value = quote(value, safe='')
                path.append(value)
            else:
                assert isinstance(el.name, str) and el.name, 'Invalid element name %s' % el.name
                path.append(el.name)
        
        if invoker.isCollection: path.append('')
        elif invoker.node:
            assert isinstance(invoker.node, Node), 'Invalid node %s' % invoker.node
            if invoker.node.hasMandatorySlash: path.append('')
        uri = '/'.join(path)
        
        if self.extension: uri = '%s.%s' % (uri, self.extension)
        if self.handler.resourcesRootURI: uri = self.handler.resourcesRootURI % uri
        if self.encoderPath: uri = self.encoderPath.encode(uri)
        
        return uri
    
    def encodePattern(self, path, invalid=None, **keyargs):
        '''
        @see: EncoderPath.encodePattern
        
        @param invalid: @see: Path.toPaths
            The callable to handle invalid matches.
        '''
        # TODO: Gabriel: update for invoker
        if isinstance(path, Path):
            assert isinstance(path, Path)
            
            uri, paths = [], path.toPaths(self.handler.converterPath, invalid=invalid)
            
            if self.handler.patternPrefix is None: uri.append('\\/'.join(paths))
            else: uri.append('\\/'.join(chain(self.handler.patternPrefix, paths, self.handler.patternSuffix)))
            if self.extension:
                uri.append('\\.')
                uri.append(self.extension)
            uri = ''.join(uri)
            
            if self.wrapped: return self.wrapped.encodePattern(uri, **keyargs)
            assert not keyargs, 'Invalid key arguments %s' % keyargs
            return uri
        
        elif self.wrapped is None:
            assert invalid is not None, 'No invalid replacer expected %s' % invalid
            assert not keyargs, 'Invalid key arguments %s' % keyargs
            return path
        
        return self.wrapped.encodePattern(path, **keyargs)
        
