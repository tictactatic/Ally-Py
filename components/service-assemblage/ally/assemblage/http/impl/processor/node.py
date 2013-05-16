'''
Created on Apr 5, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the node structure to be assembled.
'''

from ally.assemblage.http.spec.assemblage import RequestNode
from ally.container.ioc import injected
from ally.design.processor.attribute import defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import HeaderCmx, HeadersRequire
from ally.support.util import lastCheck

# --------------------------------------------------------------------

ASSEMBLAGE = HeaderCmx('X-Filter', False)
# The header name for the assemblage request.

# --------------------------------------------------------------------

class Request(HeadersRequire):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Optional
    parameters = optional(list)
    
class Assemblage(Context):
    '''
    The assemblage context.
    '''
    # ---------------------------------------------------------------- Defined
    requestNode = defines(RequestNode, doc='''
    @rtype: RequestNode
    The main request node to be assembled.
    ''')

# --------------------------------------------------------------------

@injected
class RequestNodeHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the node structure to be assembled.
    '''

    def process(self, chain, request:Request, assemblage:Assemblage, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the node structure assemblage.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        
        values = ASSEMBLAGE.decodeOnce(request)
        if not values: return  # No assemblage requested.
        # First we adjust the request node tree.
        
        assemblage.requestNode = RequestNode()
        for name in values:
            current = assemblage.requestNode
            for name in name.split('.'):
                subnode = current.requests.get(name)
                if subnode is None: subnode = current.requests[name] = RequestNode()
                current = subnode
        
        if Request.parameters not in request or not request.parameters: return  # No parameters to process.
        # We process the parameters for each node request.
        for name, value in request.parameters:
            current = assemblage.requestNode
            names = name.split('.')
            for k, (isLast, name) in enumerate(lastCheck(names)):
                if isLast: current.parameters.append((name, value))
                else:
                    subnode = current.requests.get(name)
                    if subnode is None:
                        current.parameters.append(('.'.join(names[k:]), value))
                    else: current = subnode
                    
        request.parameters = assemblage.requestNode.parameters
