'''
Created on Jul 19, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides specifications for indexes. 
'''

# --------------------------------------------------------------------

NAME_BLOCK = 'general'  # The general block name.

# --------------------------------------------------------------------

ACTION_STREAM = 'stream'  # The action name for streaming a block.
ACTION_DISCARD = 'discard'  # The action name for discarding a block.
ACTION_INJECT = 'inject'  # The action name for injecting in a block.
ACTION_NAME = 'get_name'  # The action name for providing the block name.

# --------------------------------------------------------------------

class Index:
    '''
    Specification for an index.
    '''
    __slots__ = ('block', 'values')
    
    def __init__(self, block, values=None):
        '''
        Construct the index.
        
        @param block: string
            The index block name.
        @param values: dictionary{string: integer|string}
            The values of the index.
        '''
        assert isinstance(block, str), 'Invalid index block name %s' % block
        if values is None: values = {}
        assert isinstance(values, dict), 'Invalid values %s' % values
        
        self.block = block
        self.values = values
        
