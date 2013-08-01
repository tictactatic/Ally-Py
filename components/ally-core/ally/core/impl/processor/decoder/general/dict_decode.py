'''
Created on Jul 26, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the dictionary decoding.
'''

from ally.api.type import Type, Dict
from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires, attribute, \
    optional
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Abort
from ally.design.processor.handler import HandlerBranching
from ally.support.util_spec import IDo
import logging
from ally.core.impl.processor.base import FailureTarget, addFailure

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    parent = defines(Context, doc='''
    @rtype: Context
    The parent decoding that this decoding is based on.
    ''')
    doDecode = defines(IDo, doc='''
    @rtype: callable(target, value)
    Decodes the value into the provided target.
    @param target: Context
        Target context object used for decoding.
    @param value: dictionary{object: object}
        The dictionary value to be decoded.
    ''')
    isMandatory = defines(bool, doc='''
    @rtype: boolean
    Indicates that the decoding needs to have a value provided.
    ''')
    # ---------------------------------------------------------------- Optional
    doBegin = optional(IDo)
    doEnd = optional(IDo)
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    doSet = requires(IDo)
    doGet = requires(IDo)
    
# --------------------------------------------------------------------

@injected
class DictDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the dictionary decoding.
    '''
    
    dictItemAssembly = Assembly
    # The dictionary item processors.
    
    def __init__(self):
        assert isinstance(self.dictItemAssembly, Assembly), 'Invalid item assembly %s' % self.dictItemAssembly
        super().__init__(Branch(self.dictItemAssembly).included(), Target=FailureTarget)

    def process(self, chain, processing, decoding:Decoding, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Populate the dictionary decoder.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if decoding.doDecode: return
        if not isinstance(decoding.type, Dict): return  # The type is not a list, just move along.
        assert isinstance(decoding.type, Dict)
        
        idecoding = decoding.__class__()
        assert isinstance(idecoding, Decoding), 'Invalid decoding %s' % idecoding
        
        idecoding.parent = decoding
        idecoding.isMandatory = True
        idecoding.doSet = self.createSetItem(decoding.doGet, decoding.doSet)
        
        arg = processing.execute(decoding=idecoding, **keyargs)
        assert isinstance(arg.decoding, Decoding), 'Invalid decoding %s' % arg.decoding
        if arg.decoding.doDecode:
            decoding.doDecode = self.createDecode(arg.decoding, decoding)
        else:
            log.error('Cannot decode dictionary item %s', decoding.type)
            raise Abort(decoding)
        
    # ----------------------------------------------------------------
    
    def createSetItem(self, getter, setter):
        '''
        Create the do set for the dictionary item.
        '''
        assert isinstance(getter, IDo), 'Invalid getter %s' % getter
        assert isinstance(setter, IDo), 'Invalid setter %s' % setter
        def doSet(target, item):
            '''
            Do set the dictionary item value.
            '''
            key, value = item
            previous = getter(target)
            if previous is None: setter(target, {key: value})
            else:
                assert isinstance(previous, dict), 'Invalid previous value %s' % previous
                previous[key] = value
        return doSet
    
    def createDecode(self, idecoding, decoding):
        '''
        Create the do decode for dictionary.
        '''
        assert isinstance(idecoding, Decoding), 'Invalid decoding %s' % idecoding
        decode = idecoding.doDecode
        if Decoding.doBegin in idecoding: begin = idecoding.doBegin
        else: begin = None
        if Decoding.doEnd in idecoding: end = idecoding.doEnd
        else: end = None
        assert isinstance(decode, IDo), 'Invalid decode %s' % decode
        assert begin is None or isinstance(begin, IDo), 'Invalid begin %s' % begin
        assert end is None or isinstance(end, IDo), 'Invalid end %s' % end
        def doDecode(target, value):
            '''
            Do decode the dictionary.
            '''
            assert isinstance(idecoding, Decoding)
            if not isinstance(value, dict): addFailure(target, decoding, value=value)
            else:
                assert isinstance(value, dict)
                for item in value.items():
                    if begin: begin(target)
                    decode(target, item)
                    if end: end(target)
        return doDecode

# --------------------------------------------------------------------

class DecodingItem(Context):
    '''
    The decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    isMandatory = defines(bool, doc='''
    @rtype: boolean
    Indicates that the decoding needs to have a value provided.
    ''')
    doBegin = defines(IDo, doc='''
    @rtype: callable(target)
    Required to be triggered in order to begin the decoding.
    @param target: Context
        Target context object that the decoding begins on.
    ''')
    doDecode = defines(IDo, doc='''
    @rtype: callable(target, value)
    Decodes the value into the provided target.
    @param target: Context
        Target context object used for decoding.
    @param value: tuple(object, object)
        The dictionary item value to be decoded.
    ''')
    doEnd = defines(IDo, doc='''
    @rtype: callable(target)
    Required to be triggered in order to end the decoding.
    @param target: Context
        Target context object that the decoding ends on.
    ''')
    doGet = defines(IDo)
    # ---------------------------------------------------------------- Required
    parent = requires(Context)
    type = requires(Type)
    doSet = requires(IDo)
    
class TargetItem(FailureTarget):
    '''
    The target context.
    '''
    # ---------------------------------------------------------------- Defined
    dictEntryKey = attribute(object, doc='''
    @rtype: object
    The dictionary entry key.
    ''')
    dictEntryValue = attribute(object, doc='''
    @rtype: boolean
    The dictionary entry value.
    ''')

# --------------------------------------------------------------------

@injected
class DictItemDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the dictionary item decoding.
    '''
    
    itemKeyAssembly = Assembly
    # The dictionary key decode processors to be used for decoding.
    itemValueAssembly = Assembly
    # The dictionary value decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.itemKeyAssembly, Assembly), 'Invalid key assembly %s' % self.dictKeyAssembly
        assert isinstance(self.itemValueAssembly, Assembly), 'Invalid value assembly %s' % self.dictValueAssembly
        super().__init__(Branch(self.itemKeyAssembly).included(), Branch(self.itemValueAssembly).included(),
                         Target=TargetItem)

    def process(self, chain, processingKey, processingValue, decoding:DecodingItem, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Populate the dictionary decoder.
        '''
        assert isinstance(processingKey, Processing), 'Invalid processing %s' % processingKey
        assert isinstance(processingValue, Processing), 'Invalid processing %s' % processingValue
        assert isinstance(decoding, DecodingItem), 'Invalid decoding %s' % decoding
        
        if decoding.doDecode: return
        if not decoding.parent: return
        assert isinstance(decoding.parent, DecodingItem), 'Invalid decoding %s' % decoding.parent
        if not isinstance(decoding.parent.type, Dict): return  # The type is not a list, just move along.
        assert isinstance(decoding.parent.type, Dict)
        
        kdecoding, vdecoding = decoding.__class__(), decoding.__class__()
        assert isinstance(kdecoding, DecodingItem), 'Invalid decoding %s' % kdecoding
        assert isinstance(vdecoding, DecodingItem), 'Invalid decoding %s' % vdecoding
        
        kdecoding.parent = decoding
        kdecoding.isMandatory = True
        kdecoding.type = decoding.parent.type.keyType
        kdecoding.doSet, kdecoding.doGet = self.doSetKey, self.doGetKey
        
        vdecoding.parent = decoding
        vdecoding.isMandatory = True
        vdecoding.type = decoding.parent.type.valueType
        vdecoding.doSet, vdecoding.doGet = self.doSetValue, self.doGetValue
        
        karg = processingKey.execute(decoding=kdecoding, **keyargs)
        varg = processingValue.execute(decoding=vdecoding, **keyargs)
        assert isinstance(karg.decoding, DecodingItem), 'Invalid decoding %s' % karg.decoding
        assert isinstance(varg.decoding, DecodingItem), 'Invalid decoding %s' % varg.decoding
        
        if not karg.decoding.doDecode:
            log.error('Cannot decode dictionary key %s', decoding.parent.type.keyType)
            raise Abort(decoding)
        
        if not varg.decoding.doDecode:
            log.error('Cannot decode dictionary value %s', decoding.parent.type.valueType)
            raise Abort(decoding)
        
        decoding.doBegin = self.doBegin
        decoding.doDecode = self.createDecode(karg.decoding.doDecode, varg.decoding.doDecode, decoding)
        decoding.doEnd = self.createEnd(decoding.doSet)
        
    # ----------------------------------------------------------------
    
    def doSetKey(self, target, value):
        '''
        Do set the dictionary key.
        '''
        assert isinstance(target, TargetItem), 'Invalid target %s' % target
        target.dictEntryKey = value
    
    def doGetKey(self, target):
        '''
        Do get the dictionary key.
        '''
        assert isinstance(target, TargetItem), 'Invalid target %s' % target
        return target.dictEntryKey
        
    def doSetValue(self, target, value):
        '''
        Do set the dictionary value.
        '''
        assert isinstance(target, TargetItem), 'Invalid target %s' % target
        target.dictEntryValue = value

    def doGetValue(self, target):
        '''
        Do get the dictionary value.
        '''
        assert isinstance(target, TargetItem), 'Invalid target %s' % target
        return target.dictEntryValue

    def doBegin(self, target):
        '''
        Do begin for the dictionary item.
        '''
        assert isinstance(target, TargetItem), 'Invalid target %s' % target
        target.dictEntryKey = target.dictEntryValue = None
    
    def createDecode(self, decodeKey, decodeValue, decoding):
        '''
        Create the do decode for dictionary item.
        '''
        assert isinstance(decodeKey, IDo), 'Invalid decode %s' % decodeKey
        assert isinstance(decodeValue, IDo), 'Invalid decode %s' % decodeValue
        def doDecode(target, value):
            '''
            Do decode the dictionary item.
            '''
            assert isinstance(target, TargetItem), 'Invalid target %s' % target
            if not isinstance(value, tuple) or len(value) != 2: addFailure(target, decoding, value=value)
            else:
                decodeKey(target, value[0])
                decodeValue(target, value[1])
        return doDecode
    
    def createEnd(self, setter):
        '''
        Create the do end for dictionary item.
        '''
        assert isinstance(setter, IDo), 'Invalid setter %s' % setter
        def doEnd(target):
            '''
            Do end the dictionary item.
            '''
            assert isinstance(target, TargetItem), 'Invalid target %s' % target
            if target.dictEntryKey is None: return
            if target.dictEntryValue is None: return
            setter(target, (target.dictEntryKey, target.dictEntryValue))
            
        return doEnd
