'''
Created on Jul 26, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the solved marking for the decoding.
'''

from ally.api.type import Input
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
    # ---------------------------------------------------------------- Defined
    solved = defines(set, doc='''
    @rtype: set(object)
    The input of the caller that are solved on the invoker.
    ''')
    
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

class MarkSolvedHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the solved marking for decoding.
    '''
        
    def process(self, chain, decoding:Decoding, invoker:Invoker, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Mark the solved decodings decoding.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        
        if not decoding.doDecode: return
        inp = findFirst(decoding, Decoding.parent, Decoding.input)
        assert isinstance(inp, Input), 'Invalid input %s' % inp

        if invoker.solved is None: invoker.solved = set()
        invoker.solved.add(inp)
