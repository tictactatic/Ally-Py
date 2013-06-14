'''
Created on Aug 2, 2012

@package: ally api
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides standard extended objects.
'''

from .config import extension
from collections import Iterable

# --------------------------------------------------------------------
#TODO: rename to IterSlice
@extension
class IterPart(Iterable):
    '''
    Provides a wrapping for iterable objects that represent a part of a bigger collection. Basically beside the actual
    items this class objects also contain a total count of the big item collection that this iterable is part of.
    '''
    total = int
    offset = int
    limit = int

    def __init__(self, wrapped, total, offset=None, limit=None):
        '''
        Construct the partial iterable.
        
        @param wrapped: Iterable
            The iterable that provides the actual data.
        '''
        assert isinstance(wrapped, Iterable), 'Invalid iterable %s' % wrapped
        assert isinstance(total, int), 'Invalid total %s' % total
        assert total >= 0, 'Invalid total value %s' % total
        assert offset is None or isinstance(offset, int), 'Invalid offset %s' % offset
        assert limit is None or isinstance(limit, int), 'Invalid limit %s' % limit
        
        if offset is None or offset < 0: offset = 0
        elif offset > total: offset = total
        if limit is None: limit = total - offset
        elif limit > total - offset: limit = total - offset

        self.wrapped = wrapped
        self.total = total
        self.offset = offset
        self.limit = limit

    def __iter__(self): return self.wrapped.__iter__()

    def __str__(self):
        return '%s[%s(%s:%s), %s]' % (self.__class__.__name__, self.total, self.offset, self.limit, self.wrapped)

#TODO: temporary for rename to IterSlice
IterSlice = IterPart