'''
Created on Apr 25, 2013

@package: ally indexing
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the modifications perform support.
'''

from ..spec.model import Action, Perform
from ..spec.modifier import Content, IModifier, IAlter
from .perform_do import hasFlags
from ally.support.util_io import IInputStream
from collections import deque, Iterable
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class ModifierByIndex(IModifier):
    '''
    The modifier based on indexes.
    '''
    __slots__ = ('_content', '_processors', '_first', '_last', '_index', '_actions', '_registered', '_final')
        
    def __init__(self, processors, content, first=(), last=()):
        '''
        Construct the modifier based on indexes.
        
        @param content: Content
            The content to modify.
        @param processors: dictionary{string: callable}
            The dictionary of do perform prepare processors calls indexed by verb name.
        @param first: tuple(string)
            The default actions to be executed first in the block.
        @param last: tuple(string)
            The default actions to be executed last in the block.
        '''
        assert isinstance(processors, dict), 'Invalid processors %s' % processors
        assert isinstance(content, Content), 'Invalid content %s' % content
        assert isinstance(content.source, IInputStream), 'Invalid content source %s' % content.source
        assert callable(content.doDecode), 'Invalid content decode %s' % content.doDecode
        assert isinstance(content.indexes, list), 'Invalid content indexes %s' % content.indexes
        assert isinstance(first, tuple), 'Invalid first defaults %s' % first
        assert isinstance(last, tuple), 'Invalid last defaults %s' % last
        if __debug__:
            for name in first: assert isinstance(name, str), 'Invalid first action name %s' % name
            for name in last: assert isinstance(name, str), 'Invalid last action name %s' % name
            for name, call in processors.items():
                assert isinstance(name, str), 'Invalid do verb name %s' % name
                assert callable(call), 'Invalid do  processor call %s' % call
        
        self._processors = processors
        self._content = content
        self._first = first
        self._last = last
        self._actions = set()
        self._registered = deque()
        
    def fetch(self, name):
        '''
        @see: Modifier.fetch
        '''
        assert isinstance(name, str), 'Invalid action name %s' % name
        
        for action in self._index.block.actions:
            assert isinstance(action, Action), 'Invalid action %s' % action
            if action.name == name and not action.final:
                prepared = self._prepare(action)
                if prepared:
                    byts = b''.join(self._process(action, prepared, {}, set()))
                    return self._content.doDecode(byts)
    
    def register(self, *names, value=None):
        '''
        @see: Modifier.register
        '''
        if not names: return False
        
        registered = False
        for name in names:
            assert isinstance(name, str), 'Invalid action name %s' % name
            if self._final: break
            
            for action in self._index.block.actions:
                assert isinstance(action, Action), 'Invalid action %s' % action
                if action.name == name:
                    prepared = self._prepare(action, value)
                    if not prepared: return registered
                    for nameBefore in action.before:
                        if nameBefore not in self._actions: self.register(nameBefore)
                    assert not self._final, 'One of the before actions %s is a final one' % action.before
                    self._actions.add(action.name)
                    self._registered.append((action, prepared))
                    self._final = action.final
                    registered = True
        return registered
    
    # ----------------------------------------------------------------
    
    def process(self, alter, values, flags):
        '''
        Process the registered actions.
        '''
        assert isinstance(alter, IAlter), 'Invalid alter %s' % alter
        
        for index in self._content.indexes:
            self._registered.clear()
            self._actions.clear()
            self._final = False
            self._index = index
            
            self.register(*self._first)
            alter.alter(self._content, self)
            self.register(*self._last)
            
            for action, prepared in self._registered:
                for pack in self._process(action, prepared, values, flags): yield pack
                
        self._content.source.close()  # We need to ensure that we close the response source.
    
    def _prepare(self, action, value=None):
        '''
        Prepare the processors for action and value.
        
        @param action: Action
            The action to prepare.
        @param value: object|None
            The value to prepare for.
        @return: list[callable}|None
            The list of prepared processors calls, or None if preparing has failed.
        '''
        assert isinstance(action, Action), 'Invalid action %s' % action
        
        prepared = []
        for perform in action.performs:
            assert isinstance(perform, Perform), 'Invalid perform %s' % perform
            
            prepare = self._processors.get(perform.verb)
            if prepare is None:
                assert log.error('Unknown verb \'%s\'', perform.verb) or True
                return
            processor = prepare(self._index, perform, value)
            if processor is None:
                assert log.error('Cannot prepare processor for verb \'%s\' with content \'%s\'',
                                 perform.verb, value) or True
                return
            assert callable(processor), 'Invalid processor %s' % processor
            prepared.append(processor)
        return prepared
    
    def _process(self, action, prepared, values, flags):
        '''
        Process the action with context.
        
        @param action: Action
            The action to process.
        @param prepared: dictionary{string: callable}
            The prepared processor calls indexed by verb name.
        '''
        assert isinstance(action, Action), 'Invalid action %s' % action
        assert isinstance(prepared, list), 'Invalid prepared processors %s' % prepared
        
        if action.rewind: self._content.source.record()
        
        for processor in prepared:
            value = processor(self._content, values, flags)
            if value is None: continue
            if isinstance(value, bytes):
                if value == b'': continue
                yield value
            else:
                assert isinstance(value, Iterable), 'Invalid value %s' % value
                for pack in value:
                    assert isinstance(pack, bytes), 'Invalid pack %s for value %s' % (pack, value)
                    if pack == b'': continue
                    yield pack
            
        if action.rewind: self._content.source.rewind()

# --------------------------------------------------------------------

def iterateModified(alter, processors, content, *defaults):
    '''
    Iterate the modified content.
    
    @param alter: IAlter
        The alter to be used with the modifiers.
    @param processors: dictionary{string: callable}
        The dictionary of do perform prepare processors calls indexed by verb name.
    @param content: Content
        The content to modify.
    @param defaults: arguments[string]
        The default actions to be registered for every block.
    '''
    assert isinstance(alter, IAlter), 'Invalid alter %s' % alter
    processors = dict(processors)
    
    def feedIndexed(index, perform, value):
        '''
        Stream proxy side indexed content action perform.
        '''
        if value is None: return
        if not isinstance(value, (str, Content)): return
        if isinstance(value, Content):
            assert isinstance(value, Content)
            if not isinstance(value.source, IInputStream): return
            if not callable(value.doDecode) or not callable(value.doEncode): return
            if not value.indexes: return
            
        def do(content, values, flags):
            if not hasFlags(perform, flags): return
            assert isinstance(perform, Perform), 'Invalid perform %s' % perform
            return ModifierByIndex(processors, value, first=perform.actions, last=defaults).process(alter, values, set())
        return do
    if feedIndexed.__name__ not in processors: processors[feedIndexed.__name__] = feedIndexed

    return ModifierByIndex(processors, content, last=defaults).process(alter, {}, set())
