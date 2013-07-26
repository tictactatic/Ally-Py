'''
Created on Jul 19, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoker decoding.
'''

from ally.api.type import Input, Type
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Abort
from ally.design.processor.handler import HandlerBranching
from ally.support.util_spec import IDo
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)
    solved = requires(set)
    location = requires(str)

class Create(Context):
    '''
    The create decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    decodings = defines(list, doc='''
    @rtype: list[Context]
    The list of decoding contexts to be processed.
    ''')
    
class DecodingRequest(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    input = defines(Input, doc='''
    @rtype: Input
    The input that the create is for.
    ''')
    type = defines(Type, doc='''
    @rtype: Type
    The type to be decoded.
    ''')
    doSet = defines(IDo, doc='''
    @rtype: callable(target, value)
    Set the constructed value into the provided target.
    @param target: Context
        The target context to set the value to.
    @param value: object
        The value object to set to the target.
    ''')
    doGet = defines(IDo, doc='''
    @rtype: callable(target) -> object
    Get the value represented by the constructor from the provided target.
    @param target: Context
        The target context to get the value from.
    @return: object
        The object from the target.
    ''')
    
class Target(Context):
    '''
    The target context.
    '''
    # ---------------------------------------------------------------- Required
    arguments = requires(dict)
      
# --------------------------------------------------------------------

@injected
class DecodingHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the creation of decoders for invokers.
    '''
    
    decodeAssembly = Assembly
    # The decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.decodeAssembly, Assembly), 'Invalid decode assembly %s' % self.decodeAssembly
        super().__init__(Branch(self.decodeAssembly).using(create=Create).
                         included(('node', 'Node'), ('invoker', 'Invoker')).included(),
                         Invoker=Invoker, Target=Target)

    def process(self, chain, processing, register:Register, Decoding:DecodingRequest, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Process the decoding.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Decoding, DecodingRequest), 'Invalid decoding class %s' % Decoding
        if not register.invokers: return  # No invokers to process.

        aborted = []
        keyargs.update(register=register, Decoding=Decoding)
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            if invoker.inputs:
                decodings = []
                for inp in invoker.inputs:
                    assert isinstance(inp, Input), 'Invalid input %s' % inp
                    
                    if invoker.solved and inp in invoker.solved: continue  # Already solved
                    
                    decoding = Decoding()
                    decodings.append(decoding)
                    assert isinstance(decoding, DecodingRequest), 'Invalid decoding %s' % decoding
                    
                    decoding.input = inp
                    decoding.type = inp.type
                    decoding.doGet = self.createGet(inp.name)
                    decoding.doSet = self.createSet(inp.name)

                if decodings:
                    keyargs.update(node=invoker.node, invoker=invoker)
                    try: processing.executeWithAll(create=processing.ctx.create(decodings=decodings), **keyargs)
                    except Abort:
                        log.error('Cannot use because there is no valid decoder for %s, at:%s',
                                  decoding.input, invoker.location)
                        aborted.append(invoker)
                                        
        if aborted: raise Abort(*aborted)

    # ----------------------------------------------------------------
    
    def createGet(self, key):
        '''
        Create the do get.
        '''
        assert isinstance(key, str), 'Invalid key %s' % key
        def doGet(target):
            '''
            Do get the value from arguments.
            '''
            assert isinstance(target, Target), 'Invalid target %s' % target
            assert isinstance(target.arguments, dict), 'Invalid arguments %s' % target.arguments
            return target.arguments.get(key)
        return doGet
        
    def createSet(self, key):
        '''
        Create the do set.
        '''
        assert isinstance(key, str), 'Invalid key %s' % key
        def doSet(target, value):
            '''
            Do set the value to arguments.
            '''
            assert isinstance(target, Target), 'Invalid target %s' % target
            assert isinstance(target.arguments, dict), 'Invalid arguments %s' % target.arguments
            target.arguments[key] = value
        return doSet

