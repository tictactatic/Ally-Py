'''
Created on Jun 28, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the URI request node handler.
'''

from ally.core.spec.resources import Converter
from ally.design.processor.attribute import requires, defines, definesIf
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import PATH_FOUND, PATH_NOT_FOUND, CodedHTTP, \
    MISSING_SLASH
from ally.support.core.util_resources import valueOfAny
from urllib.parse import unquote
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    root = requires(Context)
    
class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    byName = requires(dict)
    byType = requires(dict)
    properties = requires(set)
    invokers = requires(dict)
    hasMandatorySlash = requires(bool)

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    node = defines(Context, doc='''
    @rtype: Context
    The node corresponding to the request.
    ''')
    pathValues = definesIf(dict, doc='''
    @rtype: dictionary{TypeProperty: object}
    A dictionary containing the path values indexed by the node properties.
    ''')
    extension = defines(str, doc='''
    @rtype: string
    The extension of the requested URI.
    ''')
    arguments = definesIf(dict, doc='''
    @rtype: dictionary{Type|string: object}
    A dictionary containing the arguments to be used for the invoking.
    ''')
    # ---------------------------------------------------------------- Required
    scheme = requires(str)
    uri = requires(str)
    converterPath = requires(Converter)

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

class URIHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the searches based on the request URI the resource node, also
    populates the arguments based on path and extension on the request.
    '''

    def __init__(self):
        super().__init__(Node=Node)

    def process(self, chain, register:Register, request:Request, response:CodedHTTP, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the URI to a resource path.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(request, Request), 'Invalid required request %s' % request
        assert isinstance(response, CodedHTTP), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        if response.isSuccess is False: return  # Skip in case the response is in error
        assert isinstance(request.uri, str), 'Invalid request URI %s' % request.uri
        assert isinstance(request.converterPath, Converter), 'Invalid request converter %s' % request.converterPath
        
        paths = request.uri.split('/')
        i = paths[-1].rfind('.') if len(paths) > 0 else -1
        if i < 0:
            clearExtension = True
            request.extension = None
        else:
            clearExtension = i == 0
            request.extension = paths[-1][i + 1:].lower()
            paths[-1] = paths[-1][0:i]
        
        paths = [unquote(p) for p in paths if p]

        if request.extension: responseCnt.type = request.extension
        
        node = register.root
        for path in paths:
            assert isinstance(node, Node), 'Invalid node %s' % node
            if node.byName:
                assert isinstance(node.byName, dict), 'Invalid by name %s' % node.byName
                node = node.byName.get(path)
            elif node.byType:
                assert isinstance(node.byType, dict) and node.byType, 'Invalid node by type %s' % node.byType
                try: value, typeValue = valueOfAny(request.converterPath, path, node.byType)
                except ValueError:
                    assert log.debug('Invalid value \'%s\' for: %s', path, ','.join(str(typ) for typ in node.byType)) or True
                    node = None
                else:
                    node = node.byType[typeValue]
                    if Request.arguments in request:
                        assert isinstance(node.properties, set), 'Invalid properties types %s' % node.properties
                        if request.arguments is None: request.arguments = {}
                        for propType in node.properties: request.arguments[propType] = value
                    if Request.pathValues in request:
                        assert isinstance(node.properties, set), 'Invalid properties types %s' % node.properties
                        if request.pathValues is None: request.pathValues = {}
                        for propType in node.properties: request.pathValues[propType] = value
            else: node = None

            if node is None: break
                
        if node is None or not node.invokers:
            PATH_NOT_FOUND.set(response)
            assert log.debug('No resource found for URI %s', request.uri) or True
            return
        
        if not clearExtension and node.hasMandatorySlash:
            # We need to check if the last path element is not a string property ant there might be confusion
            # with the extension
            MISSING_SLASH.set(response)
            assert log.debug('Unclear extension for URI %s', request.uri) or True
            return
                
        assert log.debug('Found resource for URI %s', request.uri) or True
        PATH_FOUND.set(response)
        request.node = node
