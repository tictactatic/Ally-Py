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
from ally.core.http.spec.transform.encdec import CATEGORY_PARAMETER
from ally.core.spec.resources import Converter
from ally.core.spec.transform.encdec import IDecoder
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import CodedHTTP

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    decoder = requires(IDecoder)
    categoriesDecoded = requires(set)
    definitions = requires(list)
    
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    parameters = requires(list)
    invoker = requires(Context)
    arguments = requires(dict)
    converterPath = requires(Converter)

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    errorMessages = defines(list)

class SupportDecoding(Context):
    '''
    The decoder support context.
    '''
    # ---------------------------------------------------------------- Defined
    category = defines(object, doc='''
    @rtype: object
    The category of the ongoing decoding.
    ''')
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to be used for decoding.
    ''')
    # ---------------------------------------------------------------- Required
    failures = requires(list)

# --------------------------------------------------------------------

@injected
class ParameterHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the transformation of parameters into arguments.
    '''

    def __init__(self):
        super().__init__(Invoker=Invoker)

    def process(self, chain, request:Request, response:Response, Support:SupportDecoding, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the parameters into arguments.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error

        if not request.invoker: return  # No invoker available
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        
        if request.parameters:
            illegal = set()
            
            decoder = request.invoker.decoder
            if not decoder: illegal.update(name for name, value in request.parameters)
            else:
                assert isinstance(decoder, IDecoder), 'Invalid decoder %s' % decoder
                
                if request.arguments is None: request.arguments = {}
                support = Support(category=CATEGORY_PARAMETER, converter=request.converterPath)
                assert isinstance(support, SupportDecoding), 'Invalid support %s' % support
                
                for name, value in request.parameters:
                    if not decoder.decode(name, value, request.arguments, support): illegal.add(name)
                    
            if illegal or support.failures:
                PARAMETER_ILLEGAL.set(response)
                if response.errorMessages is None: response.errorMessages = []
                
                if illegal: response.errorMessages.append('Unknown parameters: %s' % ', '.join(sorted(illegal)))
                if support.failures: response.errorMessages.extend(support.failures)
                
                if not request.invoker.categoriesDecoded or CATEGORY_PARAMETER not in request.invoker.categoriesDecoded:
                    response.errorMessages.append('\nNo parameters are available')
                
