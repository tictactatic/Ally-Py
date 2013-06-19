'''
Created on May 16, 2013

@package: ally api
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Nistor Gabriel

Provides general used options for APIs.
'''

from .config import option

# --------------------------------------------------------------------

@option
class Slice:
    '''
    Provides collection slicing options.
    '''
    
    offset = int
    limit = int
    
    def __init__(self, offset=0, limit=100):
        '''
        Construct the slice.
        
        @param offset: integer
            The start offset from where to fetch the collection.
        @param limit: integer|None
            The number of items to fetch, if None it will fetch all available items (from the provided offset).
        '''
        assert isinstance(offset, int), 'Invalid offset %s' % offset
        if offset < 0: offset = 0
        if limit is not None:
            assert isinstance(limit, int), 'Invalid limit %s' % limit
            if limit < 0: limit = 0

        self.offset = offset
        self.limit = limit

@option
class SliceAndTotal(Slice):
    '''
    Provides collection slicing options and also provides the total count option for the slice.
    '''
    
    withTotal = bool
    
    def __init__(self, withTotal=False, **slice):
        '''
        Construct the slice.
        @see: Slice.__init__
        
        @param withTotal: boolean
            Flag indicating that the total count for the slice should be provided.
        '''
        assert isinstance(withTotal, bool), 'Invalid with total flag %s' % withTotal
        Slice.__init__(self, **slice)

        self.withTotal = withTotal
