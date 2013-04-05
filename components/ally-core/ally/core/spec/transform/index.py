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

class IIndexer(metaclass=abc.ABCMeta):
    '''
    The indexer specification.
    '''
    __slots__ = ()
    
    @abc.abstractmethod
    def block(self, index, name):
        '''
        Start a block capture.
        
        @param index: integer
            The start index for the block.
        @param name: string
            The block name.
        @return: self
            The same indexer for chaining purposes.
        '''
    
    @abc.abstractmethod
    def group(self, index, name):
        '''
        Start a group capture.
        
        @param index: integer
            The start index for the group.
        @param name: string
            The group name.
        @return: self
            The same indexer for chaining purposes.
        '''
    
    @abc.abstractmethod
    def inject(self, index, value=None):
        '''
        Start an injection.
        
        @param index: integer
            The start index for the injection.
        @param value: string|None
            The value to be injected, None if the value is actually removed.
        @return: self
            The same indexer for chaining purposes.
        '''
    
    @abc.abstractmethod
    def end(self, index):
        '''
        End the current ongoing started action.
        
        @param index: integer
            The end index for the ongoing action.
        '''
    
    @abc.abstractmethod
    def represent(self):
        '''
        Create a representation of the indexed data.
        
        @return: string
            The representation of the indexes.
        '''

# --------------------------------------------------------------------

class Index:
    '''
    General index request class container that is used for informing the renderer what to index.
    '''
    __slots__ = ()

BLOCK = Index()  # capture the rendered block, this is a generic block capture based on the rendered name
PREPARE = Index()  # prepare to be injected with other REST resource content
ADJUST = Index()  # provide the injection adjusters

# --------------------------------------------------------------------

class AttrValue(Index):
    '''
    Index an attribute value capture group.
    '''
    __slots__ = ('name', 'attribute')
    
    def __init__(self, name, attribute):
        '''
        Construct the attribute value capture.
        
        @param name: string
            The group name.
        @param attribute: string
            The attribute name to capture.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(attribute, str), 'Invalid attribute %s' % attribute
        
        self.name = name
        self.attribute = attribute
