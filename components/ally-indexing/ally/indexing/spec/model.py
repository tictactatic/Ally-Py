'''
Created on Apr 25, 2013

@package: ally indexing
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the model data containers for indexes transformations. 
'''
from ally.support.util import immut

# --------------------------------------------------------------------

class Block:
    '''
    The block data container.
    '''
    __slots__ = ('actions', 'keys', 'indexes')
    
    def __init__(self, *actions, keys=None):
        '''
        Construct the block.
        
        @param actions: arguments[Action]
            The actions of the block.
        @param keys: tuple(string)|None
            The block keys names associated with the block.
        '''
        if keys is None: keys = ()
        elif not isinstance(keys, tuple): keys = tuple(keys)
        assert isinstance(keys, tuple), 'Invalid keys %s' % keys
        if __debug__:
            for key in keys: assert isinstance(key, str), 'Invalid name %s' % key
        self.actions = actions
        self.keys = keys
        
        indexes = set()
        for action in actions:
            assert isinstance(action, Action), 'Invalid action %s' % action
            for perform in action.performs:
                assert isinstance(perform, Perform), 'Invalid perform %s' % perform
                if perform.index is not None:
                    assert isinstance(perform.index, str), 'Invalid perform index \'%s\'' % perform.index
                    indexes.add(perform.index)
        self.indexes = tuple(sorted(indexes))
        
class Action:
    '''
    The action data container.
    '''
    __slots__ = ('name', 'performs', 'before', 'after', 'final', 'rewind')
    
    def __init__(self, name, *performs, before=None, final=True, rewind=False):
        '''
        Construct the action.
        
        @param name: string
            The name of the action.
        @param performs: arguments[Perform]
            The action performs.
        @param before: tuple(string)
            The action names to be triggered automatically before this action, the actions will be triggered only once
            for a block.
        @param final: boolean
            Flag indicating that the action is the final action on the block.
        @param rewind: boolean
            Flag indicating that after the action is performed the stream should be rewinded as it was before the action.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        if before is None: before = ()
        elif not isinstance(before, tuple): before = tuple(before)
        assert isinstance(before, (list, tuple)), 'Invalid before action triggers %s' % before
        assert isinstance(final, bool), 'Invalid final flag %s' % final
        assert isinstance(rewind, bool), 'Invalid rewind flag %s' % rewind
        if __debug__:
            for perform in performs: assert isinstance(perform, Perform), 'Invalid perform %s' % perform
            for trigger in before: assert isinstance(trigger, str), 'Invalid before trigger %s' % trigger
        self.name = name
        self.performs = performs
        self.before = before
        self.final = final
        self.rewind = rewind
        
class Perform:
    '''
    The action perform container.
    '''
    __slots__ = ('verb', 'flags', 'index', 'key', 'name', 'value', 'actions', 'escapes')
    
    def __init__(self, verb, *flags, index=None, key=None, name=None, value=None, actions=None, escapes=None):
        '''
        Construct the action do.
        
        @param verb: string
            The perform action verb, basically what it should do.
        @param flags: arguments[string]
            The flags associated with the action perform.
        @param index: string|None
            The index to associated with the action perform.
        @param key: string|None
            The block key to associated with the action perform.
        @param name: string|None
            The name to associated with the action perform.
        @param value: string|None
            The value to associated with the action perform.
        @param actions: tuple(string)|None
            The action names to associated with the action perform.
        @param escapes: dictionary{string: string}
            The escape dictionary, as a key the value that needs to be escaped and as a value the replacing value.
        '''
        assert isinstance(verb, str), 'Invalid verb %s' % verb
        assert index is None or isinstance(index, str), 'Invalid index %s' % index
        assert key is None or isinstance(key, str), 'Invalid key %s' % key
        assert name is None or isinstance(name, str), 'Invalid name %s' % name
        assert value is None or isinstance(value, str), 'Invalid value %s' % value
        if actions is None: actions = ()
        elif not isinstance(actions, tuple): actions = tuple(actions)
        if escapes is None: escapes = immut()
        elif not isinstance(escapes, immut): escapes = immut(escapes)
        assert isinstance(actions, tuple), 'Invalid actions %s' % actions
        assert isinstance(escapes, dict), 'Invalid escapes %s' % escapes
        if __debug__:
            for flag in flags: assert isinstance(flag, str), 'Invalid flag %s' % flag
            for action in actions: assert isinstance(action, str), 'Invalid action %s' % action
            for replaced, replacer in escapes.items():
                assert isinstance(replaced, str), 'Invalid replaced value %s' % replaced
                assert isinstance(replacer, str), 'Invalid replacer value %s' % replacer
        self.verb = verb
        self.flags = frozenset(flags)
        self.index = index
        self.key = key
        self.name = name
        self.value = value
        self.actions = actions
        self.escapes = escapes

# --------------------------------------------------------------------

class Index:
    '''
    Specification for an index.
    '''
    __slots__ = ('block', 'values')
    
    def __init__(self, block):
        '''
        Construct the index.
        
        @param block: Block
            The index block.
        '''
        assert isinstance(block, Block), 'Invalid index block %s' % block
        self.block = block
        self.values = {}
