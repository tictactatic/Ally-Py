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
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IDecoderHeader
from ally.support.util import lastCheck

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Defined
    requestNode = defines(RequestNode, doc='''
    @rtype: RequestNode
    The main request node to be assembled.
    ''')
    # ---------------------------------------------------------------- Optional
    parameters = optional(list)
    # ---------------------------------------------------------------- Required
    decoderHeader = requires(IDecoderHeader)
    headers = requires(dict)

# --------------------------------------------------------------------

@injected
class RequestedNodeHandler(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the node structure to be assembled.
    '''
    
    nameAssemblage = 'X-Filter'
    # The header name for the assemblage request.
    
    def __init__(self):
        assert isinstance(self.nameAssemblage, str), 'Invalid assemblage name %s' % self.maximum_response_length
        super().__init__()

    def process(self, request:Request, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provide the node structure.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid decoder header %s' % request.decoderHeader
        
        values = request.decoderHeader.decode(self.nameAssemblage)
        if not values: return  # No assemblage requested.
        if request.headers: request.headers.pop(self.nameAssemblage, None)  # No need to pass the assemblage header.
        # First we adjust the request node tree.
        request.requestNode = RequestNode()
        for name, _attributes in values:
            current = request.requestNode
            for name in name.split('.'):
                subnode = current.requests.get(name)
                if subnode is None: subnode = current.requests[name] = RequestNode()
                current = subnode
        
        if Request.parameters not in request or not request.parameters: return  # No parameters to process.
        # We process the parameters for each node request.
        for name, value in request.parameters:
            current = request.requestNode
            names = name.split('.')
            for k, (isLast, name) in enumerate(lastCheck(names)):
                if isLast: current.parameters.append((name, value))
                else:
                    subnode = current.requests.get(name)
                    if subnode is None:
                        current.parameters.append(('.'.join(names[k:]), value))
                    else: current = subnode