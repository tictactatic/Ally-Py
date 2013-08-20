'''
Created on Feb 23, 2013

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides support for priorities.
'''
from ally.support.util_sys import callerFrame, locationStack

# --------------------------------------------------------------------

class Priority:
    '''
    Provides priorities.
    '''
    
    def __init__(self, name, after=None, before=None, **keywords):
        '''
        Create a new priority.
 
        @param name: string
            The name for priority.
        @param after: Priority|None
            The created priority will be after the provided priority.
        @param before: Priority|None
            The created priority will be before the provided priority.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        
        self.name = name
        location = keywords.get('location')
        if location is None: self.location = locationStack(callerFrame()).strip()
        else:
            assert isinstance(location, str), 'Invalid location %s' % location
            self.location = location.strip()

        if before:
            assert isinstance(before, Priority), 'Invalid priority %s' % before
            assert after is None, 'Can only have before or after priority'
            if __debug__:
                try: assert before != PRIORITY_FIRST, 'Cannot add a priority above PRIORITY_FIRST'
                except NameError: pass

            self._group = before._group
            self._group.insert(self._group.index(before), self)
        elif after:
            assert isinstance(after, Priority), 'Invalid priority %s' % after
            if __debug__:
                try:assert before != PRIORITY_LAST, 'Cannot add a priority after PRIORITY_LAST'
                except NameError: pass
                
            self._group = after._group
            self._group.insert(self._group.index(after) + 1, self)
        else:
            self._group = [self]
            
        for k, priority in enumerate(self._group): priority._index = k
        
    group = property(lambda self: iter(self._group), doc='''
    @rtype: Iterable(Priority)
    Provides all the priorities in this priority group.
    ''')

# --------------------------------------------------------------------

PRIORITY_FIRST = Priority('First', location=locationStack(callerFrame(0)))
PRIORITY_NORMAL = Priority('Normal', after=PRIORITY_FIRST, location=locationStack(callerFrame(0)))
PRIORITY_LAST = Priority('Last', after=PRIORITY_NORMAL, location=locationStack(callerFrame(0)))

# --------------------------------------------------------------------

def sortByPriorities(itemsList, priority=None, reverse=False):
    '''
    Sorts the item list based on priorities.
    
    @param itemsList: list[object]
        The list to be sorted in place.
    @param priority: callable(object)|None
        The function that provides the priority for the provided object, if None the item list is expected to be
        of priorities.
    @param reverse: boolean
        The reverse sorting flag, same as list sort.
    '''
    assert isinstance(itemsList, list), 'Invalid item list %s' % itemsList
    assert priority is None or callable(priority), 'Invalid priority callable %s' % priority
    
    group = None
    def key(obj):
        if priority: obj = priority(obj)
        assert isinstance(obj, Priority), 'Invalid priority %s' % obj
        nonlocal group
        if group is None: group = obj._group
        assert obj._group is group, 'Invalid priority %s for group %s' % (obj, group)
        return obj._index
    itemsList.sort(key=key, reverse=reverse)
