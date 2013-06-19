'''
Created on May 17, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the slice option values handling.
'''

from ally.api.operator.type import TypeProperty
from ally.api.option import Slice, SliceAndTotal
from ally.api.type import Input, typeFor
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.api.util_service import isCompatible, isAvailableIn
from collections import Callable
from functools import partial
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    prepare = defines(Callable)
    definitions = defines(dict, doc='''
    @rtype: dictionary{frozenset: Context}
    Definitions indexed based on a frozenset containing representative data for definition.
    ''')
    # ---------------------------------------------------------------- Required
    inputs = requires(tuple)
    location = requires(str)

class DefinitionSlice(Context):
    '''
    The definition context.
    '''
    # ---------------------------------------------------------------- Defined
    description = defines(list)

# --------------------------------------------------------------------

class OptionSliceHandler(HandlerProcessor):
    '''
    Implementation for a processor that enforces collection slicing values.
    '''
    
    maximumLimit = None
    # The maximum allowed limit.
    defaultLimit = None
    # The default limit.
    defaultWithTotal = None
    # The default value for providing the total count.

    def __init__(self):
        '''
        Construct the handler.
        '''
        assert self.maximumLimit is None or isinstance(self.maximumLimit, int), 'Invalid maximum limit %s' % self.maximumLimit
        assert self.defaultLimit is None or isinstance(self.defaultLimit, int), 'Invalid default limit %s' % self.defaultLimit
        assert self.defaultWithTotal is None or isinstance(self.defaultWithTotal, bool), \
        'Invalid default with total %s' % self.defaultWithTotal
        super().__init__(Invoker=Invoker)
        
        self.typeLimit = typeFor(Slice.limit)
        self.typeTotal = typeFor(SliceAndTotal.withTotal)
        
    def process(self, chain, register:Register, Definition:DefinitionSlice, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the slicing options values.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert issubclass(Definition, DefinitionSlice), 'Invalid definition class %s' % Definition
        if not register.invokers: return  # No invokers to process
        
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if not invoker.inputs: continue
            
            compatible = None
            hasLimit = hasTotal = False
            for inp in invoker.inputs:
                assert isinstance(inp, Input), 'Invalid input %s' % inp
                
                if not isinstance(inp.type, TypeProperty):
                    if isAvailableIn(SliceAndTotal, inp.name, inp.type):
                        if compatible is None: compatible = {}
                        compatible[inp.name] = inp
                    continue
                
                descs = None
                if isCompatible(Slice.offset, inp.type):
                    if descs is None: descs = []
                    descs.append('indicates the start offset in a collection from where to retrieve')
                elif isCompatible(Slice.limit, inp.type):
                    hasLimit = True
                    if descs is None: descs = []
                    descs.append('indicates the number of entities to be retrieved from a collection')
                    if self.defaultLimit is not None:
                        descs.append('if no value is provided it defaults to %s' % self.defaultLimit)
                    if self.maximumLimit is not None: descs.append('the maximum value is %s' % self.maximumLimit)
                elif isCompatible(SliceAndTotal.withTotal, inp.type):
                    hasTotal = True
                    if descs is None: descs = []
                    descs.append('indicates that the total count of the collection has to be provided')
                    if self.defaultWithTotal is not None:
                        descs.append('if no value is provided it defaults to %s' % self.defaultWithTotal)
                        
                if descs:
                    if invoker.definitions is None: invoker.definitions = {}
                    key = frozenset((inp,))
                    definition = invoker.definitions.get(key)
                    if definition is None: definition = invoker.definitions[key] = Definition()
                    assert isinstance(definition, DefinitionSlice), 'Invalid definition %s' % definition
                    if definition.description is None: definition.description = descs
                    else: definition.description.extend(descs)
                        
            if hasLimit or hasTotal: invoker.prepare = partial(self.prepare, hasLimit, hasTotal, invoker.prepare)
            elif compatible:
                if self.typeTotal.name in compatible: clazz = SliceAndTotal
                else: clazz = Slice
                log.warn('Instead of inputs \'%s\' you could use %s.%s, at:%s', ', '.join(sorted(compatible)),
                         clazz.__module__, clazz.__name__, invoker.location)
    
    # ----------------------------------------------------------------
    
    def prepare(self, hasLimit, hasTotal, wrapped, arguments):
        '''
        Prepares the arguments for invoking.
        '''
        assert isinstance(arguments, dict), 'Invalid arguments %s' % arguments
        
        if hasLimit:
            limit = arguments.get(self.typeLimit.name)
            if limit is None: limit = arguments.get(self.typeLimit)
            if limit is None:
                if self.defaultLimit is not None: arguments[self.typeLimit.name] = self.defaultLimit
                elif self.maximumLimit is not None: arguments[self.typeLimit.name] = self.maximumLimit
            elif self.maximumLimit and limit > self.maximumLimit: arguments[self.typeLimit.name] = self.maximumLimit
            
        if hasTotal and self.defaultWithTotal is not None:
            if arguments.get(self.typeTotal.name) is None and arguments.get(self.typeTotal):
                arguments[self.typeTotal.name] = self.defaultWithTotal

