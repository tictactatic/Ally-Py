'''
Created on Jun 16, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoker base decoder.
'''

from .base import InvokerExcluded, RegisterExcluding, excludeFrom
from ally.api.type import Input
from ally.core.impl.processor.decoder.base import RequestDecoding
from ally.core.spec.transform.encdec import IDevise
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.support.util_context import findFirst
import abc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(InvokerExcluded):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    solved = defines(set, doc='''
    @rtype: set(string)
    The input names of the caller that are solved on the invoker.
    ''')
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)

class Create(Context):
    '''
    The create decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    decodings = defines(list, doc='''
    @rtype: list[Context]
    The list of decoding contexts to be processed.
    ''')
    
class DecodingBase(RequestDecoding):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    input = defines(Input, doc='''
    @rtype: Input
    The input that the create is for.
    ''')
    path = defines(list, doc='''
    @rtype: list[string]
    The path locating the created decoder.
    ''')
    # ---------------------------------------------------------------- Optional
    parent = optional(Context)
    isCorrupted = optional(bool)
    
# --------------------------------------------------------------------

class DecodingBaseHandler(HandlerBranching):
    '''
    Base implementation for a handler that provides the creation of decoders for invokers.
    '''
    
    decodeAssembly = Assembly
    # The decode processors to be used for decoding.
    
    def __init__(self, *includes, Create=Create, Definition=DecodingBase, Invoker=Invoker, **contexts):
        assert isinstance(self.decodeAssembly, Assembly), 'Invalid decode assembly %s' % self.decodeAssembly
        super().__init__(Branch(self.decodeAssembly).using(create=Create).
                         included(('Decoding', 'Definition'), ('node', 'Node'), ('invoker', 'Invoker'), *includes),
                         Invoker=Invoker, Definition=Definition, **contexts)

    def process(self, chain, processing, register:RegisterExcluding, Definition:Context, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Process the decoding.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(register, RegisterExcluding), 'Invalid register %s' % register
        assert issubclass(Definition, DecodingBase), 'Invalid definition/decoding class %s' % Definition
        if not register.invokers: return  # No invokers to process.
        
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            if invoker.inputs:
                decodings = []
                for inp in invoker.inputs:
                    assert isinstance(inp, Input), 'Invalid input %s' % inp
                    
                    if invoker.solved and inp.name in invoker.solved: continue  # Already solved
                    
                    decoding = Definition()
                    decodings.append(decoding)
                    assert isinstance(decoding, DecodingBase), 'Invalid decoding %s' % decoding
                    
                    decoding.input = inp
                    decoding.path = [inp.name]
                    decoding.devise = DeviseDecoding(inp.name)
                    decoding.type = inp.type

                if decodings:
                    keyargs.update(Decoding=Definition, node=invoker.node, invoker=invoker)
                    arg = processing.executeWithAll(create=processing.ctx.create(decodings=decodings), **keyargs)
                    assert isinstance(arg.create, Create), 'Invalid create %s' % arg.create
                    
                    if arg.create.decodings:
                        solved, decodings = set(), []
                        for decoding in arg.create.decodings:
                            assert isinstance(decoding, DecodingBase), 'Invalid decoding %s' % decoding
                            if DecodingBase.isCorrupted in decoding and decoding.isCorrupted:
                                log.error('Cannot use because there is no decoder available for %s, at:%s',
                                          decoding.input, invoker.location)
                                excludeFrom(chain, invoker)
                                break
                            elif decoding.decoder is not None:
                                inp = findFirst(decoding, DecodingBase.parent, DecodingBase.input)
                                if inp: solved.add(inp.name)
                                decodings.append(decoding)
                        else:
                            if decodings:
                                if self.index(invoker, decodings):
                                    if invoker.solved is None: invoker.solved = solved
                                    else: invoker.solved.update(solved)
                                else: excludeFrom(chain, invoker)
                        
    # ----------------------------------------------------------------
    
    @abc.abstractclassmethod
    def index(self, invoker, decodings):
        '''
        Index the decodings into the provided invoker. If other value then True is returned it means that the invoker
        needs to be excluded.
        '''

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
    
    def set(self, target, value):
        '''
        @see: IDevise.set
        '''
        assert isinstance(target, dict), 'Invalid target %s' % target
        target[self.key] = value
