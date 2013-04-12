'''
Created on Apr 4, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the indexer for rendering.
'''

from ally.container.ioc import injected
from ally.core.spec.transform.index import IIndexer, IMarkRegistry
from ally.design.processor.attribute import defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from collections import Callable
from functools import partial

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
class IndexerProviderHandler(HandlerProcessorProceed, IMarkRegistry):
    '''
    Provides the indexer for rendering.
    '''
    
    def __init__(self):
        super().__init__()
        
        self._marks = {None:encode(0)}
        self._closed = False

    def process(self, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the indexer factory
        '''
        assert isinstance(response, Response), 'Invalid response %s' % response

        self._closed = True  # The first indexer creation closes the registry
        response.indexerFactory = partial(Indexer, self._marks)
        
    # ----------------------------------------------------------------
    
    def register(self, mark, hasIndexValue=False, **data):
        '''
        @see: IMarkRegistry.register
        '''
        assert isinstance(mark, str), 'Invalid mark %s' % mark
        assert isinstance(hasIndexValue, bool), 'Invalid has index value %s' % hasIndexValue
        assert not self._closed, 'Cannot register anymore'
        
        identifier = len(self._marks) + 1
        identifier = markValue(identifier) if hasIndexValue else markNoValue(identifier)
        self._marks[mark] = hasIndexValue, encode(identifier)

# --------------------------------------------------------------------

class Indexer(IIndexer):
    '''
    Implementation for @see: IIndexer.
    '''
    __slots__ = ('_marks', '_index', '_value', '_current', '_opened')
    
    def __init__(self, marks):
        '''
        Construct the indexer.
        
        @param marks: dictionary{string: tuple(boolean, string)}
            The marks as a key and as a value a tuple with a flag indicating that in the index a value is
            expected and on the second position the marks identifier.
        '''
        assert isinstance(marks, dict), 'Invalid marks %s' % marks
        
        self._marks = marks
        self._index = []
        self._value = []
        self._current = 0
        self._opened = 0
    
    def start(self, mark, offset, value=None):
        '''
        @see: IIndexer.start
        '''
        assert isinstance(mark, str), 'Invalid mark %s' % mark
        assert mark in self._marks, 'Unknown mark %s' % mark
        assert isinstance(offset, int), 'Invalid offset %s' % offset
        assert self._current <= offset, 'Invalid offset %s is should be smaller or equal then %s' % (offset, self._current)
        
        hasValue, identifier = self._marks[mark]
        
        self._index.append(encode(offset - self._current, 2))
        self._index.append(identifier)
        if hasValue:
            if value is None: pos = 0
            else:
                assert isinstance(value, str), 'Invalid value %s' % value
                pos = len(self._value) + 1
                self._value.append((pos, value))
            self._index.append(encode(pos))
        else:
            assert value is None, 'No value expected for mark \'%s\' but got \'%s\'' % (mark, value)
       
        self._current = offset
        self._opened += 1
        
        return self
        
    def end(self, offset):
        '''
        @see: IIndexer.end
        '''
        assert isinstance(offset, int), 'Invalid offset %s' % offset
        assert self._current <= offset, 'Invalid offset %s is should be smaller or equal then %s' % (offset, self._current)
        assert self._opened > 0, 'Nothing to end'
        
        self._index.append(encode(offset - self._current, 2))
        self._index.append(self._marks[None])
        
        self._current = offset
        self._opened -= 1
        
    def represent(self):
        '''
        @see: IIndexer.represent
        '''
        assert self._opened == 0, 'Not yet finalized'
        
        values = []
        for pos, value in self._value:
            values.append(encode(pos))
            values.append(encode(len(value)))
            values.append(value)
        
        # TODO: remove
        print(len(''.join((''.join(self._index), END, ''.join(values)))))
        return ''.join((''.join(self._index), END, ''.join(values)))

# --------------------------------------------------------------------

START = 32  # The ASCII start position
COUNT = 94  # The ASCII count characters
WITH_VALUE = 1 << (len('{0:b}'.format(COUNT)) - 1)  # The mark with value for identifier, basically the first bite of COUNT
MAXIMUM = COUNT ^ WITH_VALUE  # The maximum value allowed for identifier.
END = chr(START + COUNT)  # Marker used to signal the end of a block.

def encode(value, digits=1):
    '''
    Encodes the value.
    '''
    assert value >= 0, 'Invalid value %s' % value
    assert digits >= 1, 'Invalid digits %s' % digits
    encoded = []
    while value > 0:
        encoded.append(chr(value % COUNT + START))
        value = int(value / COUNT)
    assert len(encoded) <= digits, 'Encoded value %s to large' % value 
    while len(encoded) < digits: encoded.append(chr(START))
    encoded.reverse()
    return ''.join(encoded)

def markValue(identifier):
    '''
    Adds to the identifier the marker for no value.
    '''
    assert isinstance(identifier, int), 'Invalid identifier %s' % identifier
    assert identifier <= MAXIMUM, 'Identifier cannot be greater then %s' % MAXIMUM
    return identifier | WITH_VALUE

def markNoValue(identifier):
    '''
    Adds to the identifier the marker for value.
    '''
    assert isinstance(identifier, int), 'Invalid identifier %s' % identifier
    assert identifier <= MAXIMUM, 'Identifier cannot be greater then %s' % MAXIMUM
    return identifier
    
