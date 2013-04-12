'''
Created on Apr 3, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the rendered content indexing support. 
'''

import abc

# --------------------------------------------------------------------

BLOCK = 'block'  # Capture the rendered block, this is a generic block capture based on the rendered name.
REFERENCE = 'reference'  # Indicates that the index contains a reference fore inner block content.
PREPARE = 'prepare'  # Prepare to be injected with other REST resource content.
ADJUST = 'adjust'  # Indicates that the index is used for adjusting.

# --------------------------------------------------------------------
# General do actions.
DO_CAPTURE = 'capture'  # Indicates that the index should have the value captured.
DO_INJECT = 'inject'  # Indicates that the index should have the value injected over it.

# --------------------------------------------------------------------

class IMarkRegistry(metaclass=abc.ABCMeta):
    '''
    Provides the specification for the mark registry.
    '''
    
    @abc.abstractmethod
    def register(self, mark, **data):
        '''
        Register the provided mark.

        @param mark: string
            The index mark to register the data for.
        @param data: key arguments
            The data associated with the mark, this will be used latter on by other processes.
        '''

class IIndexer(metaclass=abc.ABCMeta):
    '''
    The indexer specification.
    '''
    __slots__ = ()
    
    @abc.abstractmethod
    def start(self, mark, offset, value=None):
        '''
        Start an index.

        @param mark: string
            The index mark, attention the mark must be known for the indexer.
        @param offset: integer
            The start offset of the index.
        @param value: string|None
            A non static value that is associated with the mark.
        @return: self
            The same indexer for chaining purposes.
        '''
    
    @abc.abstractmethod
    def end(self, offset):
        '''
        End the current ongoing started index.
        
        @param offset: integer
            The end offset for the ongoing index.
        '''
    
    @abc.abstractmethod
    def represent(self):
        '''
        Create a representation of the indexed data.
        
        @return: string
            The representation of the indexes.
        '''

# --------------------------------------------------------------------
        
class AttrInject:
    '''
    Index an attribute injection.
    '''
    __slots__ = ('mark',)
    
    def __init__(self, mark):
        '''
        Construct the attribute inject.
        
        @param mark: string
            The attribute inject index mark, attention the mark must be known for the indexer.
        '''
        assert isinstance(mark, str), 'Invalid mark %s' % mark
        
        self.mark = mark

class AttrValue:
    '''
    Index an attribute value capture group.
    '''
    __slots__ = ('mark', 'attribute')
    
    def __init__(self, mark, attribute):
        '''
        Construct the attribute value capture.
        
        @param mark: string
            The attribute capture value index mark, attention the mark must be known for the indexer.
        @param attribute: string
            The attribute name to capture.
        '''
        assert isinstance(mark, str), 'Invalid mark %s' % mark
        assert isinstance(attribute, str), 'Invalid attribute %s' % attribute
        
        self.mark = mark
        self.attribute = attribute
        
# --------------------------------------------------------------------

def registerDefaultMarks(registry):
    '''
    Register the default markers defined in this module.
    
    @param registry: IMarkRegistry
        The registry to push the marks in.
    '''
    assert isinstance(registry, IMarkRegistry), 'Invalid registry %s' % registry
    
    registry.register(BLOCK, action=BLOCK, hasIndexValue=True)
    # The block has no do action is just a block.
    registry.register(ADJUST, action=ADJUST, do=DO_INJECT, value=None)
    # The default adjusting is just removing the index content.
