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
from ally.api.type import Input, typeFor, Type
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.api.util_service import isCompatible, isAvailableIn
from ally.support.util_spec import IDo

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    doSuggest = requires(IDo)

class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Required
    location = requires(str)

class Create(Context):
    '''
    The create decode context.
    '''
    # ---------------------------------------------------------------- Required
    decodings = requires(list)
      
class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    doDefault = defines(IDo, doc='''
    @rtype: callable(target)
    Placed the default value into the provided arguments.
    @param target: Context
        The target decoded.
    ''')
    # ---------------------------------------------------------------- Required
    input = requires(Input)
    type = requires(Type)
    doSet = requires(IDo)
    
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
        super().__init__(Decoding=Decoding)
        
        self.typeLimit = typeFor(Slice.limit)
        self.typeTotal = typeFor(SliceAndTotal.withTotal)
        
    def process(self, chain, create:Create, register:Register, invoker:Invoker, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the slicing options values.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        assert isinstance(register, Register), 'Invalid register %s' % register
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        
        if not create.decodings: return 
        # There is not decodings to process.
        
        compatible = None
        for decoding in create.decodings:
            assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
            
            if not isinstance(decoding.type, TypeProperty) and decoding.input:
                assert isinstance(decoding.input, Input), 'Invalid input %s' % decoding.input
                if isAvailableIn(SliceAndTotal, decoding.input.name, decoding.type):
                    if compatible is None: compatible = {}
                    compatible[decoding.input.name] = decoding.input
                continue
            
            if isCompatible(Slice.limit, decoding.type) and (self.defaultLimit is not None or self.maximumLimit is not None):
                if self.maximumLimit is not None: decoding.doSet = self.createSetLimit(decoding.doSet)
                decoding.doDefault = self.createDefaultLimit(decoding.doSet)
            elif isCompatible(SliceAndTotal.withTotal, decoding.type) and self.defaultWithTotal is not None:
                decoding.doDefault = self.createDefaultTotal(decoding.doSet)
            
        if compatible:
            if self.typeTotal.name in compatible: clazz = SliceAndTotal
            else: clazz = Slice
            assert isinstance(register.doSuggest, IDo), 'Invalid do suggest %s' % register.doSuggest
            register.doSuggest('Instead of inputs \'%s\' you could use %s.%s, at:%s', ', '.join(sorted(compatible)),
                               clazz.__module__, clazz.__name__, invoker.location)

    # ----------------------------------------------------------------
    
    def createSetLimit(self, setter):
        '''
        Create the do set limit.
        '''
        assert isinstance(setter, IDo), 'Invalid setter %s' % setter
        def doSet(target, value):
            '''
            Do set the value but only until maximum value.
            '''
            assert isinstance(value, int), 'Invalid value %s' % value
            
            if value > self.maximumLimit: value = self.maximumLimit
            setter(target, value)
        return doSet
    
    def createDefaultLimit(self, setter):
        '''
        Create the do default limit.
        '''
        assert isinstance(setter, IDo), 'Invalid setter %s' % setter
        def doDefault(target):
            '''
            Do set the default limit value.
            '''
            if self.defaultLimit is not None: setter(target, self.defaultLimit)
            else: setter(target, self.maximumLimit)
        return doDefault
    
    def createDefaultTotal(self, setter):
        '''
        Create the do default total.
        '''
        assert isinstance(setter, IDo), 'Invalid setter %s' % setter
        def doDefault(target):
            '''
            Do set the total default value.
            '''
            setter(target, self.defaultWithTotal)
        return doDefault
