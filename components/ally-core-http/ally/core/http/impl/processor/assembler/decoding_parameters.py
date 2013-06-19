'''
Created on Jun 16, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoker parameter decoder.
'''

from ally.api.type import Input, Type
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IDecoder, IDevise, DeviseDict, \
    DecoderDelegate
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
    decoderParameters = defines(IDecoder, doc='''
    @rtype: IDecoder
    The parameters decoder.
    ''')
    definitionParameters = defines(Context, doc='''
    @rtype: Context
    The parameters definitions.
    ''')
    solved = defines(set, doc='''
    @rtype: set(string)
    The input names of the caller that are solved on the invoker.
    ''')
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)

class DefinitionParameters(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    isOptional = defines(bool, doc='''
    @rtype: boolean
    If True the definition value is optional.
    ''')
    description = defines(list, doc='''
    @rtype: list[string]
    The definition description, each entry is a paragraph line.
    ''')

class Create(Context):
    '''
    The create decoder context.
    '''
    # ---------------------------------------------------------------- Defined
    solicitaions = defines(list, doc='''
    @rtype: list[Context]
    The solicitations for creating decoders.
    ''')
    definition = defines(Context, doc='''
    @rtype: Context
    The root definition of the create.
    ''')
    # ---------------------------------------------------------------- Required
    decoders = requires(list)
    
class SolicitaionParameters(Context):
    '''
    The decoder solicitaion context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(object, doc='''
    @rtype: object
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
    key = defines(frozenset, doc='''
    @rtype: frozenset
    The frozenset that defines the create key, mainly used for definition.
    ''')
    definition = defines(Context, doc='''
    @rtype: Context
    The definition parent for solicitaion.
    ''')
    
# --------------------------------------------------------------------

@injected
class DecodingParametersHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the creation of parameters decoders for invokers.
    '''
    
    decodeAssembly = Assembly
    # The decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.decodeAssembly, Assembly), 'Invalid decode assembly %s' % self.decodeAssembly
        super().__init__(Branch(self.decodeAssembly).using(create=Create).
                         included(('invoker', 'Invoker'), ('node', 'Node')).included(), Invoker=Invoker)

    def process(self, chain, processing, register:Register, Definition:DefinitionParameters,
                Solicitaion:SolicitaionParameters, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Populate the decoder.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Definition, DefinitionParameters), 'Invalid definition class %s' % Definition
        assert issubclass(Solicitaion, SolicitaionParameters), 'Invalid solicitaion class %s' % Solicitaion
        if not register.invokers: return  # No invokers to process.
        
        keyargs.update(Definition=Definition, Solicitaion=Solicitaion)
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            definition = invoker.definitionParameters = Definition(isOptional=True, description=[])
            assert isinstance(definition, DefinitionParameters), 'Invalid definition %s' % definition
            desc = 'No parameters are available for this URL'
            if invoker.inputs:
                create = processing.ctx.create()
                assert isinstance(create, Create), 'Invalid create %s' % create
                create.definition = definition

                solved = set()
                for inp in invoker.inputs:
                    assert isinstance(inp, Input), 'Invalid input %s' % inp
                    
                    if invoker.solved and inp.name in invoker.solved: continue  # Already solved
                    solved.add(inp.name)
                    
                    sol = Solicitaion()
                    assert isinstance(sol, SolicitaionParameters), 'Invalid solicitaion %s' % sol
                    if create.solicitaions is None: create.solicitaions = []
                    create.solicitaions.append(sol)
                    
                    sol.path = inp.name
                    sol.devise = DeviseDict(inp.name)
                    sol.objType = inp.type
                    sol.key = frozenset((inp,))
                    sol.definition = definition
                
                arg = processing.executeWithAll(create=create, node=invoker.node, invoker=invoker, **keyargs)
                assert isinstance(arg.create, Create), 'Invalid create %s' % arg.create
                if arg.create.decoders:
                    invoker.decoderParameters = DecoderDelegate(arg.create.decoders)
                    
                    if invoker.solved is None: invoker.solved = set()
                    if arg.create.solicitaions:
                        for sol in arg.create.solicitaions:
                            assert isinstance(sol, SolicitaionParameters), 'Invalid solicitaion %s' % sol
                            solved.discard(sol.path)
                    invoker.solved.update(solved)
                    
                    desc = 'The available parameters of this URL'

            definition.description.append(desc)
