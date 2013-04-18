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
    __slots__ = ('id', 'name', 'group', 'action', 'target', 'escapes', 'values', 'sourceId')
    
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
        
        self.name = obj['Name']
        assert isinstance(self.name, str), 'Invalid name %s' % self.name
        
        self.group = obj['Group']
        assert isinstance(self.group, str), 'Invalid group %s' % self.group
        
        self.action = obj.get('Action')
        assert self.action is None or isinstance(self.action, str), 'Invalid action %s' % self.action
        
        self.target = obj.get('Target')
        assert self.target is None or isinstance(self.target, str), 'Invalid target %s' % self.target
        
        self.escapes = obj.get('Escapes')
        assert self.escapes is None or isinstance(self.escapes, dict), 'Invalid escapes %s' % self.escapes
        
        self.values = obj.get('Values')
        assert self.values is None or isinstance(self.values, list), 'Invalid values %s' % self.values
        
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

def isValidFor(index, group=None, action=None, target=None, hasSource=None):
    '''
    Checks if the index is valid for the provided parameters.
    
    @param group: string|None
        The group to check for, if None then all groups are considered valid.
    @param action: string|None
        The action to check for, if None then all actions are considered valid.
    @param target: string|None
        The target to check for, if None then all targets are considered valid.
    @param hasSource: boolean|None
        The index is required (True) to have a source or not to have one (False), if None then is valid 
        regardless if it has or not a source.
    @return: boolean
        True if the index is valid for the provided filtering arguments, False otherwise.
    '''
    assert isinstance(index, Index), 'Invalid index %s' % index
    assert isinstance(index.marker, Marker), 'Invalid index marker %s' % index.marker
    assert group is None or isinstance(group, str), 'Invalid group %s' % group
    assert action is None or isinstance(action, str), 'Invalid action %s' % action
    assert target is None or isinstance(target, str), 'Invalid target %s' % target
    assert hasSource is None or isinstance(hasSource, bool), 'Invalid has source flag %s' % hasSource
    
    if group is not None and index.marker.group != group: return False
    if action is not None and index.marker.action != action: return False
    if target is not None and index.marker.target != target: return False
    if hasSource is not None:
        if hasSource:
            if index.marker.sourceId is None: return False
        else:
            if index.marker.sourceId is not None: return False
    return True

def findFor(indexes, **filter):
    '''
    Finds the index for the provided filter.
    
    @param indexes: Iterable(Index)
        The iterable of indexes to search in.
    @param filter: key arguments of string
        The filter arguments, @see: isValidFor
    @return: Index|None
        The found index or None.
    '''
    assert isinstance(indexes, Iterable), 'Invalid indexes %s' % indexes
    
    for index in indexes:
        if isValidFor(index, **filter): return index

def listFor(indexes, **filter):
    '''
    Lists the indexes for the provided filter.
    
    @param indexes: Iterable(Index)
        The iterable of indexes to search in.
    @param filter: key arguments of string
        The filter arguments, @see: isValidFor
    @return: list[Index]
        The list of inject indexes.
    '''
    assert isinstance(indexes, Iterable), 'Invalid indexes %s' % indexes
    
    filtered = []
    for index in indexes:
        if isValidFor(index, **filter): filtered.append(index)
        
    return filtered

def iterWithInner(indexes, **filter):
    '''
    Iterates the indexes for the provided filter arguments.
    
    @param indexes: Iterable(Index)
        The iterable of indexes to search in.
    @param filter: key arguments of string
        The filter arguments, @see: isValidFor
    @return: Iterable(tuple(Index, list[Index]))
        Iterates the tuples containing on the first position the index that respects the filtering arguments
        and on the second the list of sub indexes regardless of their nature.
    '''
    assert isinstance(indexes, Iterable), 'Invalid indexes %s' % indexes
    
    indexes = iter(indexes)
    try: index = next(indexes)
    except StopIteration: return
    while True:
        if isValidFor(index, **filter):
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
