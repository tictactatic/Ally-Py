'''
Created on Jul 30, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the creation and organization of decoded path.
'''

from ally.api.operator.type import TypeProperty
from ally.api.type import Input, Type
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Abort
from ally.design.processor.handler import HandlerBranching
from ally.support.util_spec import IDo
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    decodingsPath = defines(dict, doc='''
    @rtype: dictionary{Context: Context}
    The decoding dictionary to be used in decoding the path values indexed by node context.
    ''')
    solved = defines(set, doc='''
    @rtype: set(object)
    The input of the caller that are solved on the invoker.
    ''')
    # ---------------------------------------------------------------- Required
    path = requires(list)

class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    node = requires(Context)
    input = requires(Input)

class Create(Context):
    '''
    The create decode context.
    '''
    # ---------------------------------------------------------------- Required
    decodings = requires(list)
    pathInjected = requires(dict)
    
class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Required
    input = requires(Input)
    type = requires(Type)
    doDecode = requires(IDo)

# --------------------------------------------------------------------

@injected
class CreatePathHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the creation of decoded path.
    '''
    
    decodePathAssembly = Assembly
    # The decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.decodePathAssembly, Assembly), \
        'Invalid content decode assembly %s' % self.decodePathAssembly
        super().__init__(Branch(self.decodePathAssembly).included(('decoding', 'Decoding')).included(),
                         Decoding=Decoding, Element=Element)
    
    def process(self, chain, processing, create:Create, invoker:Invoker, **keyargs):
        '''
        HandlerBranching.process
        
        Process the path decoding.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        if not invoker.path: return 
        
        nodeDecoding = {}
        if create.decodings:
            for decoding in create.decodings:
                assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
                if decoding.doDecode: continue
                if not decoding.input: continue
                assert isinstance(decoding.input, Input), 'Invalid input %s' % decoding.input
                
                for el in invoker.path:
                    assert isinstance(el, Element), 'Invalid path element %s' % el
                    if el.node and el.input == decoding.input:
                        assert isinstance(decoding.type, TypeProperty), 'Invalid input type %s' % decoding.type
                        decoding.type = decoding.type.type
                        nodeDecoding[el.node] = decoding
                        if invoker.solved is None: invoker.solved = set()
                        invoker.solved.add(decoding.input)
                        break
        
        if create.pathInjected: nodeDecoding.update(create.pathInjected)
                
        if nodeDecoding:         
            keyargs.update(create=create, invoker=invoker)
            for node, decoding in nodeDecoding.items():
                arg = processing.execute(decoding=decoding, **keyargs)
                assert isinstance(arg.decoding, Decoding), 'Invalid decoding %s' % arg.decoding
                
                if arg.decoding.doDecode:
                    if invoker.decodingsPath is None: invoker.decodingsPath = {}
                    invoker.decodingsPath[node] = arg.decoding
                else:
                    log.error('Cannot decode path item %s', decoding.input.type)
                    raise Abort(decoding)
