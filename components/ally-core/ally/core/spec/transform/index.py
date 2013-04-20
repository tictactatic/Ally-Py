'''
Created on Apr 17, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides general specifications for indexes. 
'''

# --------------------------------------------------------------------

NAME_BLOCK = 'block'  # The marker name for block.
NAME_ADJUST = 'adjust'  # The marker name for adjust.

# --------------------------------------------------------------------

GROUP_BLOCK = 'block'  # The group name for block.
# The group name for markers that are used for joining blocks, this type of marker has to be on only one
# index per response and have a value to be used in joining the blocks.  .
GROUP_BLOCK_JOIN = 'block join'
GROUP_BLOCK_ADJUST = 'block adjust'  # The group name for adjusting the content between blocks.
GROUP_PREPARE = 'prepare'  # The group name for prepare.
GROUP_ADJUST = 'adjust'  # The group name for adjust.

# --------------------------------------------------------------------

ACTION_INJECT = 'inject'  # The action name for inject.
ACTION_CAPTURE = 'capture'  # The action name for capture.

# --------------------------------------------------------------------

PLACE_HOLDER = '${%s}'  # Used for creating place holders.
PLACE_HOLDER_CONTENT = ''  # The values entry that marks the proxy side content.

# --------------------------------------------------------------------

# Provides the general markers definitions.
GENERAL_MARKERS = {
                   NAME_BLOCK: dict(group=GROUP_BLOCK),
                   NAME_ADJUST: dict(group=GROUP_ADJUST, action=ACTION_INJECT),
                   }

# --------------------------------------------------------------------

class Index:
    '''
    Index data container.
    '''
    __slots__ = ('name', 'start', 'end', 'value')
    
    def __init__(self, name, start, value):
        '''
        Construct the index.
        
        @param name: string
            The marker name of the index.
        @param start: integer
            The start of the index.
        @param value: string|None
            The value of the index.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(start, int), 'Invalid start offset %s' % start
        assert value is None or isinstance(value, str), 'Invalid value %s' % value
        
        self.name = name
        self.start = start
        self.end = start
        self.value = value
