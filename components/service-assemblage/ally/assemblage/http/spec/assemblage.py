'''
Created on Feb 7, 2013

@package: assemblage service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the assemblage specification.
'''

from ally.support.util import immut
from collections import Iterable

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

class Marker:
    '''
    Provides the marker data constructed based on object.
    '''
    __slots__ = ('id', 'group', 'action', 'sourceId')
    
    def __init__(self, obj):
        '''
        Construct the marker based on the provided dictionary object.
        @see: assemblage/assemblage.api.marker
        
        @param obj: dictionary{string: string|list[string]}
            The dictionary used for defining the marker object, the object as is defined from response.
        '''
        assert isinstance(obj, dict), 'Invalid object %s' % obj
        
        id = obj['Id']
        assert isinstance(id, str), 'Invalid id %s' % id
        self.id = int(id)
        
        self.group = obj['Group']
        assert isinstance(self.group, str), 'Invalid group %s' % self.group
        
        self.action = obj.get('Action')
        assert self.action is None or isinstance(self.action, str), 'Invalid action %s' % self.action
        
        sourceId = obj.get('Source', immut()).get('Id')
        if sourceId is not None:
            assert isinstance(sourceId, str), 'Invalid source id %s' % sourceId
            self.sourceId = int(sourceId)
        else: self.sourceId = None

class Index:
    '''
    Container for an index.
    '''
    __slots__ = ('marker', 'start', 'end', 'value')
    
    def __init__(self, marker, start, value=None):
        '''
        Construct the index.
        
        @param marker: Marker
            The marker for the index.
        @param start: integer
            The start of the index.
        @param value: string|None
            The value for the index.
        @ivar end: integer
            The end of the index, by default is the start index.
        '''
        assert isinstance(marker, Marker), 'Invalid marker %s' % marker
        assert isinstance(start, int), 'Invalid start index %s' % start
        assert value is None or isinstance(value, str), 'Invalid value %s' % value
        
        self.marker = marker
        self.start = start
        self.end = start
        self.value = value

# --------------------------------------------------------------------
            
def listFor(indexes, group=None, action=None):
    '''
    Lists the inject indexes.
    
    @param indexes: Iterable(Index)
        The iterable of indexes to search in.
    @param group: string|None
        The group to search for, if None then all groups are considered valid.
    @param action: string|None
        The action to search for, if None then all actions are considered valid.
    @return: list[Index]
        The list of inject indexes.
    '''
    assert isinstance(indexes, Iterable), 'Invalid indexes %s' % indexes
    assert group is None or isinstance(group, str), 'Invalid group %s' % group
    assert action is None or isinstance(action, str), 'Invalid action %s' % action
    
    filtered = []
    for index in indexes:
        assert isinstance(index, Index), 'Invalid index %s' % index
        assert isinstance(index.marker, Marker), 'Invalid index marker %s' % index.marker
        
        valid = True
        if group and index.marker.group != group: valid = False
        elif action and index.marker.action != action: valid = False
        if valid: filtered.append(index)
        
    return filtered

def iterWithInner(indexes, group=None, action=None):
    '''
    Iterates the indexes for the provided filter parameters.
    
    @param indexes: Iterable(Index)
        The iterable of indexes to search in.
    @param group: string|None
        The group to search for, if None then all groups are considered valid.
    @param action: string|None
        The action to search for, if None then all actions are considered valid.
    @return: Iterable(tuple(Index, list[Index]))
        Iterates the tuples containing on the first position the index that respects the filtering parameters
        and on the second the list of sub indexes regardless of their nature.
    '''
    assert isinstance(indexes, Iterable), 'Invalid indexes %s' % indexes
    assert group is None or isinstance(group, str), 'Invalid group %s' % group
    assert action is None or isinstance(action, str), 'Invalid action %s' % action
    
    indexes = iter(indexes)
    try: index = next(indexes)
    except StopIteration: return
    while True:
        assert isinstance(index, Index), 'Invalid index %s' % index
        assert isinstance(index.marker, Marker), 'Invalid index marker %s' % index.marker
        valid = True
        if group and index.marker.group != group: valid = False
        elif action and index.marker.action != action: valid = False
        
        if valid:
            inner, finalized = [], False
            while True:
                try: iindex = next(indexes)
                except StopIteration:
                    finalized = True
                    break
                assert isinstance(iindex, Index), 'Invalid index %s' % iindex
                if iindex.end <= index.end: inner.append(iindex)
                else: break
            yield index, inner
            if finalized: break
            index = iindex
        else:
            try: index = next(indexes)
            except StopIteration: break
