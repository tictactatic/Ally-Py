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
from ally.core.impl.processor.decoder.base import importTarget
from ally.core.spec.resources import Converter
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import Handler, push
from ally.design.processor.processor import Contextual, Using
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
    converterPath = requires(Converter)

class TargetParameter(Context):
    '''
    The target context.
    '''
    # ---------------------------------------------------------------- Defined
    arg = defines(object, doc='''
    @rtype: object
    The ongoing chain arguments do decode the parameters based on.
    ''')
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to be used for decoding parameters.
    ''')
    # ---------------------------------------------------------------- Required
    failures = requires(list)
    
# --------------------------------------------------------------------

@injected
class ParameterHandler(Handler):
    '''
    Implementation for a processor that provides the transformation of parameters into arguments.
    '''
    
    decodeExportAssembly = Assembly
    # The decode export assembly.

    def __init__(self):
        Target, arg = importTarget(self.decodeExportAssembly)
        processor = push(Contextual(self.process), Invoker=Invoker, Decoding=Decoding, Definition=Definition)
        if arg: push(processor, **arg)
        super().__init__(Using(processor, Target=Target))

    def process(self, chain, request:Request, response:ErrorResponseHTTP, Target:TargetParameter, **keyargs):
        '''
        Process the parameters into arguments.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
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
            
            target = Target(arg=chain.arg, converter=request.converterPath)
            assert isinstance(target, TargetParameter), 'Invalid target %s' % target
            
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
            
            if target.failures:
                PARAMETER_INVALID.set(response)
                
                for name, definitions, values, messages in self.indexFailures(target.failures):
                    addError(response, messages, 'Invalid values \'%(values)s\' for \'%(name)s\'', definitions,
                             name=name, values=values)
                
        if illegal:
            PARAMETER_ILLEGAL.set(response)
            addError(response, 'Unknown parameters %(parameters)s', parameters=sorted(illegal))
                
    # --------------------------------------------------------------------
    
    def indexFailures(self, failures):
        '''
        Indexes the failures, iterates (name, definitions, values, messages)
        '''
        assert isinstance(failures, list), 'Invalid failures %s' % failures
        
        indexed = {}
        for decoding, value, messages, data in failures:
            assert value is not None, 'None value is not allowed'
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            
            defin = findFirst(decoding, Decoding.parent, Decoding.parameterDefinition)
            assert isinstance(defin, Definition), 'Invalid definition %s for %s' % (defin, decoding)
            assert isinstance(defin.name, str), 'Invalid definition name %s' % defin.name
            
            byName = indexed.get(defin.name)
            if byName is None: byName = indexed[defin.name] = ([], [], [])
            
            defins, values, msgs = byName
            defins.append(defin)
            values.append(value)
            msgs.extend(msg % data for msg in messages)
        
        for name in sorted(indexed):
            yield (name,) + indexed[name]
