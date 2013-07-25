'''
Created on Jul 19, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the organization of decoded content.
'''

from ally.api.type import Input
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires, optional
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Abort
from ally.design.processor.handler import HandlerBranching
from ally.support.util_context import findFirst
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
    decodingContent = defines(Context, doc='''
    @rtype: Context
    The decoding to be used in decoding the content values.
    ''')

class Create(Context):
    '''
    The create decode context.
    '''
    # ---------------------------------------------------------------- Required
    decodings = requires(list)
    
class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Optional
    parent = optional(Context)
    # ---------------------------------------------------------------- Required
    input = requires(Input)
    doDecode = requires(IDo)
      
# --------------------------------------------------------------------

@injected
class CreateContentDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the creation of decoded content.
    '''
    
    decodeContentAssembly = Assembly
    # The decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.decodeContentAssembly, Assembly), \
        'Invalid content decode assembly %s' % self.decodeContentAssembly
        super().__init__(Branch(self.decodeContentAssembly).
                         included(('Support', 'SupportDecodeContent'), ('decoding', 'Decoding')).included(),
                         Decoding=Decoding)
    
    def process(self, chain, processing, create:Create, invoker:Invoker, **keyargs):
        '''
        HandlerBranching.process
        
        Process the content decoding.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        if not create.decodings: return
        
        keyargs.update(create=create, invoker=invoker)
        for decoding in create.decodings:
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            if decoding.doDecode: continue
            
            arg = processing.execute(decoding=decoding, **keyargs)
            assert isinstance(arg.decoding, Decoding), 'Invalid decoding %s' % arg.decoding
            if not arg.decoding.doDecode: continue
        
            if invoker.decodingContent:
                log.error('Cannot use because there are more then one content inputs %s, %s',
                          findFirst(invoker.decodingContent, Decoding.parent, Decoding.input),
                          findFirst(decoding, Decoding.parent, Decoding.input))
                raise Abort(invoker.decodingContent, decoding)
        
            invoker.decodingContent = arg.decoding
