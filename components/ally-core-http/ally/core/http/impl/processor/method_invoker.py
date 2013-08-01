'''
Created on Jul 14, 2011

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the requested method validation handler.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.http.impl.processor.base import ErrorResponseHTTP
from ally.core.impl.processor.base import addError
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.export import Import
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import METHOD_NOT_AVAILABLE, PATH_ERROR
from ally.support.util_spec import IDo

# --------------------------------------------------------------------

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(dict)

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    decodingsPath = requires(dict)

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    doDecode = requires(IDo)
     
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    invoker = defines(Context, doc='''
    @rtype: Context
    The invoker corresponding to the request.
    ''')
    # ---------------------------------------------------------------- Required
    method = requires(str)
    node = requires(Context)
    nodeValues = requires(dict)
    converterPath = requires(Converter)

class Response(ErrorResponseHTTP):
    '''
    The response context.
    '''
    allows = defines(set)
    
class TargetPath(Context):
    '''
    The target context.
    '''
    # ---------------------------------------------------------------- Defined
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to be used for decoding path.
    ''')
    # ---------------------------------------------------------------- Required
    failures = requires(list)
    
# --------------------------------------------------------------------

@injected
class MethodInvokerHandler(HandlerProcessor):
    '''
    Implementation for a processor that validates if the request method (GET, POST, PUT, DELETE) is compatible
    with the resource node of the request, basically checks if the node has the invoke for the requested method.
    If the node has no invoke than this processor will provide an error response for the resource path node.
    '''
    
    importDecoding = Import
    # The decoding imports to be used for path.
    
    def __init__(self):
        assert isinstance(self.importDecoding, Import), 'Invalid import %s' % self.importDecoding
        super().__init__(Node=Node, Invoker=Invoker, Decoding=Decoding)
        self.importDecoding.useIn(self)

    def process(self, chain, request:Request, response:Response, Target:TargetPath, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the invoker based on the request method to be used in getting the data for the response.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert issubclass(Target, TargetPath), 'Invalid target class %s' % Target
        if response.isSuccess is False: return  # Skip in case the response is in error

        assert isinstance(request.node, Node), 'Invalid request node %s' % request.node
        assert isinstance(request.node.invokers, dict) and request.node.invokers, \
        'Invalid request node invokers %s' % request.node.invokers
        
        request.invoker = request.node.invokers.get(request.method)
        if request.invoker is None:
            if response.allows is None: response.allows = set()
            response.allows.update(request.node.invokers)
            METHOD_NOT_AVAILABLE.set(response)
            return
        
        if not request.nodeValues: return
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        if not request.invoker.decodingsPath: return
        
        target = Target(arg=chain.arg, converter=request.converterPath)
        assert isinstance(target, TargetPath), 'Invalid target %s' % target

        for node, decoding in request.invoker.decodingsPath.items():
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            assert isinstance(decoding.doDecode, IDo), 'Invalid do decode %s' % decoding.doDecode
            decoding.doDecode(target, request.nodeValues[node])
            
        if target.failures:
            PATH_ERROR.set(response)
            for type, values, messages in self.indexFailures(target.failures):
                addError(response, 'Expected type \'%(type)s\' instead of: %(values)s', messages, type=type, values=values)
        
    # --------------------------------------------------------------------
    
    def indexFailures(self, failures):
        '''
        Indexes the failures, iterates (type, values, messages)
        '''
        assert isinstance(failures, list), 'Invalid failures %s' % failures
        
        indexed = {}
        for decoding, value, messages, data in failures:
            assert value is not None, 'None value is not allowed'
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            
            byType = indexed.get(decoding.type)
            if byType is None: byType = indexed[decoding.type] = ([], [])
            
            values, msgs = byType
            values.append(value)
            msgs.extend(msg % data for msg in messages)
        
        for type, byType in indexed.items():
            yield (type,) + byType
            
