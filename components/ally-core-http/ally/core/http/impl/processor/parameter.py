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
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_context import findFirst
from ally.support.util_spec import IDo

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    decodingsParameter = requires(dict)

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Optional
    parent = optional(Context)
    # ---------------------------------------------------------------- Required
    parameterDefinition = requires(Context)
    doDecode = requires(IDo)
    doDefault = requires(IDo)

class Definition(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    
class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    parameters = requires(list)
    invoker = requires(Context)
    arguments = requires(dict)
    converterPath = requires(Converter)

class TargetParameter(Context):
    '''
    The target context.
    '''
    # ---------------------------------------------------------------- Defined
    arguments = defines(dict, doc='''
    @rtype: dictionary{string: object}
    The arguments do decode the parameters in.
    ''')
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to be used for decoding parameters.
    ''')
    doFailure = defines(IDo, doc='''
    @rtype: callable(Context, object)
    The call to use in reporting parameters decoding failures.
    ''')
    
# --------------------------------------------------------------------

@injected
class ParameterHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the transformation of parameters into arguments.
    '''

    def __init__(self):
        super().__init__(Invoker=Invoker, Decoding=Decoding, Definition=Definition)

    def process(self, chain, request:Request, response:ErrorResponseHTTP, Target:TargetParameter, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the parameters into arguments.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert issubclass(Target, TargetParameter), 'Invalid target class %s' % Target
        if response.isSuccess is False: return  # Skip in case the response is in error

        if not request.invoker: return  # No invoker available
        assert isinstance(request.invoker, Invoker), 'Invalid invoker %s' % request.invoker
        
        illegal = None
        decodings = request.invoker.decodingsParameter
        if not decodings:
            if request.parameters: illegal = set(name for name, value in request.parameters)
        else:
            assert isinstance(decodings, dict), 'Invalid decodings %s' % decodings
            
            failures = {}
            
            if request.arguments is None: request.arguments = {}
            target = Target()
            assert isinstance(target, TargetParameter), 'Invalid target %s' % target
            target.arguments = request.arguments
            target.converter = request.converterPath
            target.doFailure = self.createFailure(failures)
            
            visited = set()
            if request.parameters:
                for name, value in request.parameters:
                    decoding = decodings.get(name)
                    if decoding is None:
                        if illegal is None: illegal = set()
                        illegal.add(name)
                    else:
                        assert isinstance(decoding, Decoding), 'Invalid decoding definition %s' % decoding
                        assert isinstance(decoding.doDecode, IDo), 'Invalid do decode %s' % decoding.doDecode
                        decoding.doDecode(target, value)
                        visited.add(name)
                    
            for name, decoding in decodings.items():
                if name not in visited and decoding.doDefault: decoding.doDefault(target)
            
            if failures:
                PARAMETER_INVALID.set(response)
                
                for name in sorted(failures):
                    definitions, values = failures[name]
                    addError(response, 'Invalid values \'%(values)s\' for \'%(name)s\'', definitions, name=name, values=values)
                
        if illegal:
            PARAMETER_ILLEGAL.set(response)
            addError(response, 'Unknown parameters %(parameters)s', parameters=sorted(illegal))
                
    # --------------------------------------------------------------------
    
    def createFailure(self, failures):
        '''
        Creates the do failure.
        '''
        assert isinstance(failures, dict), 'Invalid failures %s' % failures
        def doFailure(decoding, value):
            '''
            Index the failure.
            '''
            assert value is not None, 'None value is not allowed'
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            
            defin = findFirst(decoding, Decoding.parent, Decoding.parameterDefinition)
            assert isinstance(defin, Definition), 'Invalid definition %s for %s' % (defin, decoding)
            assert isinstance(defin.name, str), 'Invalid definition name %s' % defin.name
            
            byName = failures.get(defin.name)
            if byName is None: byName = failures[defin.name] = ([], [])
            
            definitions, values = byName
            definitions.append(defin)
            values.append(value)
        return doFailure
