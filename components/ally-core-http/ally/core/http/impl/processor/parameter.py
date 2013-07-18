'''
Created on May 25, 2012

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the parameters handler.
'''

from ally.container.ioc import injected
from ally.core.http.impl.processor.base import ErrorResponseHTTP
from ally.core.http.spec.codes import PARAMETER_ILLEGAL, PARAMETER_INVALID
from ally.core.impl.processor.base import addError
from ally.core.spec.transform.encdec import IDecoder
from ally.design.processor.attribute import requires, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerComposite
from ally.design.processor.processor import Structure
from ally.support.util_context import findFirst, pushIn, cloneCollection

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    decodingParameters = requires(dict)

class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Optional
    parent = optional(Context)
    # ---------------------------------------------------------------- Required
    name = requires(str)
    decoder = requires(IDecoder)
    
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    parameters = requires(list)
    invoker = requires(Context)
    arguments = requires(dict)

class Support(Context):
    '''
    The support context.
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
        super().__init__(Structure(SupportDecodeParameter='request'), Invoker=Invoker, Definition=Definition)

    def process(self, chain, request:Request, response:ErrorResponseHTTP, SupportDecodeParameter:Support, **keyargs):
        '''
        @see: HandlerComposite.process
        
        Process the parameters into arguments.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        if response.isSuccess is False: return  # Skip in case the response is in error

        if not request.invoker: return  # No invoker available
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        
        if request.parameters:
            illegal = set()
            
            decodings = request.invoker.decodingParameters
            if not decodings: illegal.update(name for name, value in request.parameters)
            else:
                assert isinstance(decodings, dict), 'Invalid decodings %s' % decodings
                
                support = pushIn(SupportDecodeParameter(), request, interceptor=cloneCollection)
                assert isinstance(support, Support), 'Invalid support %s' % support
                if request.arguments is None: request.arguments = {}
                for name, value in request.parameters:
                    decoding = decodings.get(name)
                    if decoding is None: illegal.add(name)
                    else:
                        assert isinstance(decoding, Definition), 'Invalid decoding %s' % decoding
                        assert isinstance(decoding.decoder, IDecoder), 'Invalid decoder %s' % decoding.decoder
                        decoding.decoder.decode(value, request.arguments, support)
                
                if support.failures:
                    PARAMETER_INVALID.set(response)
                    
                    decodingByName, valuesByName = {}, {}
                    for value, decoding in support.failures:
                        name = findFirst(decoding, Definition.parent, Definition.name)
                        if name:
                            byName = decodingByName.get(name)
                            if byName is None: byName = decodingByName[name] = []
                            byName.append(decoding)
                            
                            byName = valuesByName.get(name)
                            if byName is None: byName = valuesByName[name] = []
                            byName.append(value)
                    
                    for name in sorted(valuesByName):
                        addError(response, 'Invalid values %(values)s for \'%(name)s\'',
                                 decodingByName[name], name=name, values=valuesByName[name])
                    
            if illegal:
                PARAMETER_ILLEGAL.set(response)
                addError(response, 'Unknown parameters %(parameters)s', parameters=sorted(illegal))
                
