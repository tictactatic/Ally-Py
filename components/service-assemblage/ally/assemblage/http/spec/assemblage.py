'''
Created on Feb 7, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblage specification.
'''

# --------------------------------------------------------------------

BLOCK = 1  # Marker used for blocks
GROUP = 2  # Marker used for groups
LINK = 3  # Marker used for links
INJECT = 4  # Marker used for inject

# --------------------------------------------------------------------

class RequestNode:
    '''
    Container for an assemblage node request.
    '''
    __slots__ = ('parameters', 'requests')
    
    def __init__(self):
        '''
        Construct the node.
        
        @ivar parameters: list[tuple(string, string)]
            The parameters list of tuples.
        @ivar requests: dictionary{string: RequestNode}
            The sub requests of this request node.
        '''
        self.parameters = []
        self.requests = {}

class Index:
    '''
    Container for an index.
    '''
    __slots__ = ('mark', 'start', 'end', 'value')
    
    def __init__(self, mark, start, value=None):
        '''
        Construct the index.
        
        @param mark: integer
            The mark flag for the index.
        @param start: integer
            The start of the index.
        @param value: string|None
            The value for the index.
        @ivar end: integer
            The end of the index, by default is the start index.
        '''
        assert isinstance(mark, int), 'Invalid mark %s' % mark
        assert isinstance(start, int), 'Invalid start index %s' % start
        assert value is None or isinstance(value, str), 'Invalid value %s' % value
        
        self.mark = mark
        self.start = start
        self.end = start
        self.value = value
        
    isBlock = property(lambda self: self.mark == BLOCK, doc='''
    @rtype: boolean
    True if the index is a block index.
    ''')
    isGroup = property(lambda self: self.mark == GROUP, doc='''
    @rtype: boolean
    True if the index is a group index.
    ''')
    isLink = property(lambda self: self.mark == LINK, doc='''
    @rtype: boolean
    True if the index is a link index.
    ''')
    isInject = property(lambda self: self.mark == INJECT, doc='''
    @rtype: boolean
    True if the index is an inject index.
    ''')
    
