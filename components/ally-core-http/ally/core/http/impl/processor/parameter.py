'''
Created on May 25, 2012

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the parameters handler.
'''

from ally.container.ioc import injected
from ally.core.http.spec.codes import PARAMETER_ILLEGAL
from ally.core.spec.transform.encdec import IDecoder
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context, pushIn, cloneCollection
from ally.design.processor.handler import HandlerComposite
from ally.design.processor.processor import Joiner
from ally.http.spec.codes import CodedHTTP
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    decoderParameters = requires(IDecoder)
    definitionParameters = requires(Context)
    
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    parameters = requires(list)
    invoker = requires(Context)
    arguments = requires(dict)

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    errorMessage = defines(str)
    errorDefinition = defines(Context)

class SupportDecoding(Context):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Required
    failures = requires(list)

# --------------------------------------------------------------------

@injected
class ParameterHandler(HandlerComposite):
    '''
    Implementation for a processor that provides the transformation of parameters into arguments.
    '''

    def __init__(self):
        super().__init__(Joiner(Support=('response', 'request')), Invoker=Invoker)

    def process(self, chain, request:Request, response:Response, Support:SupportDecoding, **keyargs):
        '''
        @see: HandlerComposite.process
        
        Process the parameters into arguments.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error

        if not request.invoker: return  # No invoker available
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        
        if request.parameters:
            illegal = set()
            
            decoder = request.invoker.decoderParameters
            if not decoder: illegal.update(name for name, value in request.parameters)
            else:
                assert isinstance(decoder, IDecoder), 'Invalid decoder %s' % decoder
                
                if request.arguments is None: request.arguments = {}
                support = pushIn(Support(), response, request, interceptor=cloneCollection)
                assert isinstance(support, SupportDecoding), 'Invalid support %s' % support
                for name, value in request.parameters:
                    if not decoder.decode(name, value, request.arguments, support): illegal.add(name)
                    
            if illegal or support.failures:
                PARAMETER_ILLEGAL.set(response)
                
                message = []
                if illegal: message.append('Unknown parameters: %s' % ', '.join(sorted(illegal)))
                if support.failures: message.extend(support.failures)
                
                response.errorMessage = '\n'.join(message)
                response.errorDefinition = request.invoker.definitionParameters
                return
