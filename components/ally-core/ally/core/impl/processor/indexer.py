'''
Created on Apr 4, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexer for rendering.
'''

from ally.container.ioc import injected
from ally.core.spec.transform.index import IIndexer
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from collections import Callable
import json

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    indexerFactory = defines(Callable, doc='''
    @rtype: callable() -> IIndexer
    The indexer factory to be used with the renderer. 
    ''')
    
# --------------------------------------------------------------------

@injected
class IndexerProviderHandler(HandlerProcessorProceed):
    '''
    Provides the indexer for rendering.
    '''
    
    def __init__(self):
        super().__init__()

    def process(self, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the indexer factory
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response

        response.indexerFactory = Indexer

# --------------------------------------------------------------------

class Indexer(IIndexer):
    '''
    Implementation for @see: IIndexer.
    '''
    __slots__ = ('_table', '_current', '_opened')
    
    def __init__(self):
        '''
        Construct the indexer.
        '''
        self._table = []
        self._current = 0
        self._opened = 0
    
    def block(self, index, name):
        '''
        @see: IIndexer.block
        '''
        self._process(index)
        assert isinstance(name, str), 'Invalid name %s' % name
        
        self._table.append((index, 'b', name))
        self._opened += 1
        return self
    
    def group(self, index, name):
        '''
        @see: IIndexer.group
        '''
        self._process(index)
        assert isinstance(name, str), 'Invalid name %s' % name
        
        self._table.append((index, 'g', name))
        self._opened += 1
        return self
        
    def inject(self, index, value=None):
        '''
        @see: IIndexer.inject
        '''
        self._process(index)
        assert value is None or isinstance(value, str), 'Invalid value %s' % value
        
        self._table.append((index, 'i', value))
        self._opened += 1
        return self
        
    def end(self, index):
        '''
        @see: IIndexer.end
        '''
        self._process(index)
        assert self._opened > 0, 'Nothing to end'
        
        self._table.append((index, 'e', None))
        self._opened -= 1
        
    def represent(self):
        '''
        @see: IIndexer.represent
        '''
        assert self._opened == 0, 'Not yet finalized'
        return json.dumps(self._table)

    # ----------------------------------------------------------------

    def _process(self, index):
        '''
        Process the index.
        '''
        assert isinstance(index, int), 'Invalid index %s' % index
        assert self._current <= index, 'Invalid index %s is should be smaller or equal then %s' % (index, self._current)
        
        self._current = index
        
