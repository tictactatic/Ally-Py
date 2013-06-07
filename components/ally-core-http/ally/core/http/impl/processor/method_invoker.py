'''
Created on Jul 14, 2011

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the requested method validation handler.
'''

from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import METHOD_NOT_AVAILABLE, CodedHTTP

# --------------------------------------------------------------------

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(dict)
    
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

class Response(CodedHTTP):
    '''
    The response context.
    '''
    allows = defines(set)

# --------------------------------------------------------------------

class MethodInvokerHandler(HandlerProcessor):
    '''
    Implementation for a processor that validates if the request method (GET, POST, PUT, DELETE) is compatible
    with the resource node of the request, basically checks if the node has the invoke for the requested method.
    If the node has no invoke than this processor will provide an error response for the resource path node.
    '''
    
    def __init__(self):
        super().__init__(Node=Node)

    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the invoker based on the request method to be used in getting the data for the response.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error

        assert isinstance(request.node, Node), 'Invalid request node %s' % request.node
        assert isinstance(request.node.invokers, dict) and request.node.invokers, \
        'Invalid request node invokers %s' % request.node.invokers
        
        request.invoker = request.node.invokers.get(request.method)
        if request.invoker is None:
            if response.allows is None: response.allows = set()
            response.allows.update(request.node.invokers)
            METHOD_NOT_AVAILABLE.set(response)
