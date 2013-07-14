'''
Created on Jun 16, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoker decoder.
'''

from ally.api.type import Input, Type
from ally.container.ioc import injected
from ally.core.impl.encdec import DecoderDelegate
from ally.core.spec.transform.encdec import IDecoder, IDevise
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching

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
    # ---------------------------------------------------------------- Defined
    decoder = defines(IDecoder, doc='''
    @rtype: IDecoder
    The decoder.
    ''')
    definitions = defines(list, doc='''
    @rtype: list[Context}
    Definitions containing representative data for invoker.
    ''')
    solved = defines(set, doc='''
    @rtype: set(string)
    The input names of the caller that are solved on the invoker.
    ''')
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)

class Create(Context):
    '''
    The create decoder context.
    '''
    # ---------------------------------------------------------------- Defined
    solicitations = defines(list, doc='''
    @rtype: list[Context]
    The solicitations for creating decoders.
    ''')
    # ---------------------------------------------------------------- Required
    decoders = requires(list)
    definitions = requires(list)
    
class SolicitationDecoder(Context):
    '''
    The decoder solicitation context.
    '''
    # ---------------------------------------------------------------- Defined
    invoker = defines(Context, doc='''
    @rtype: Context
    The invoker that the solicitation is based on.
    ''')
    input = defines(Input, doc='''
    @rtype: Input
    The input that the solicitation is based on.
    ''')
    path = defines(str, doc='''
    @rtype: string
    The path of the create element.
    ''')
    devise = defines(IDevise, doc='''
    @rtype: IDevise
    The devise used for constructing the decoded object.
    ''')
    objType = defines(Type, doc='''
    @rtype: Type
    The object type to be decoded.
    ''')
    
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
                         included(('invoker', 'Invoker'), ('node', 'Node')).included(), Invoker=Invoker)

    def process(self, chain, processing, register:Register, Solicitation:SolicitationDecoder, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Populate the decoder.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Solicitation, SolicitationDecoder), 'Invalid solicitation class %s' % Solicitation
        if not register.invokers: return  # No invokers to process.
        
        keyargs.update(Solicitation=Solicitation)
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            if invoker.inputs:
                create = processing.ctx.create()
                assert isinstance(create, Create), 'Invalid create %s' % create
                
                solved = set()
                for inp in invoker.inputs:
                    assert isinstance(inp, Input), 'Invalid input %s' % inp
                    
                    if invoker.solved and inp.name in invoker.solved: continue  # Already solved
                    solved.add(inp)
                    
                    sol = Solicitation()
                    assert isinstance(sol, SolicitationDecoder), 'Invalid solicitation %s' % sol
                    if create.solicitations is None: create.solicitations = []
                    create.solicitations.append(sol)
                    
                    sol.invoker = invoker
                    sol.input = inp
                    sol.path = inp.name
                    sol.devise = DeviseDecoding(inp.name)
                    sol.objType = inp.type
                
                arg = processing.executeWithAll(create=create, node=invoker.node, invoker=invoker, **keyargs)
                assert isinstance(arg.create, Create), 'Invalid create %s' % arg.create
                if arg.create.decoders:
                    invoker.decoder = DecoderDelegate(arg.create.decoders)
                    
                    if invoker.solved is None: invoker.solved = set()
                    if arg.create.solicitations:
                        for sol in arg.create.solicitations:
                            assert isinstance(sol, SolicitationDecoder), 'Invalid solicitation %s' % sol
                            solved.discard(sol.input)
                    invoker.solved.update(inp.name for inp in solved)
                
                if arg.create.definitions:
                    if invoker.definitions is None: invoker.definitions = arg.create.definitions
                    else: invoker.definitions.extend(invoker.definitions)

# --------------------------------------------------------------------

class DeviseDecoding(IDevise):
    '''
    Implementation for @see: IDevise that handles the value for a target dictionary based on a predefined key.
    '''
    __slots__ = ('key',)
    
    def __init__(self, key):
        '''
        Construct the dictionary devise.
        
        @param key: object
            The key to be used on the target dictionary.
        '''
        self.key = key
        
    def get(self, target):
        '''
        @see: IDevise.get
        
        Provides None if the key is not presssent.
        '''
        assert isinstance(target, dict), 'Invalid target %s' % target
        return target.get(self.key)
    
    def set(self, target, value, support):
        '''
        @see: IDevise.set
        '''
        assert isinstance(target, dict), 'Invalid target %s' % target
        target[self.key] = value
