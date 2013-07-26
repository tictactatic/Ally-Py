'''
Created on Jul 24, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexing for definitions.
'''

from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    definitions = defines(list, doc='''
    @rtype: list[Context]
    Definitions containing representative data for invoker decoders.
    ''')

# --------------------------------------------------------------------

class DefinitionIndexHandler(HandlerProcessor):
    '''
    Implementation for a handler that provides the indexing for definitions.
    '''
        
    def process(self, chain, invoker:Invoker, definition:Context=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Index the definition for decoding.
        '''
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        
        if not definition: return
        
        if invoker.definitions is None: invoker.definitions = []
        invoker.definitions.append(definition)
