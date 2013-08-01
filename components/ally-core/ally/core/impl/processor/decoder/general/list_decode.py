'''
Created on Jul 15, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the list decoding.
'''

from ally.api.type import List, Type
from ally.container.ioc import injected
from ally.core.impl.processor.base import FailureTarget, addFailure
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Abort
from ally.design.processor.handler import HandlerBranching
from ally.support.util_spec import IDo
import logging

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
    @param value: list[object]
        The list value to be decoded.
    ''')
    isMandatory = defines(bool, doc='''
    @rtype: boolean
    Indicates that the decoding needs to have a value provided.
    ''')
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    doSet = requires(IDo)
    doGet = requires(IDo)
    
# --------------------------------------------------------------------

@injected
class ListDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the list decoding.
    '''
    
    listItemAssembly = Assembly
    # The list item decode processors to be used for decoding.
    
    def __init__(self):
        assert isinstance(self.listItemAssembly, Assembly), 'Invalid list item assembly %s' % self.listItemAssembly
        super().__init__(Branch(self.listItemAssembly).included(), Target=FailureTarget)

    def process(self, chain, processing, decoding:Decoding, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Populate the list decoder.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if decoding.doDecode: return
        if not isinstance(decoding.type, List): return  # The type is not a list, just move along.
        assert isinstance(decoding.type, List)
        
        idecoding = decoding.__class__()
        assert isinstance(idecoding, Decoding), 'Invalid decoding %s' % idecoding
        idecoding.parent = decoding
        idecoding.type = decoding.type.itemType
        idecoding.isMandatory = True
        idecoding.doSet = self.createSetItem(decoding.doGet, decoding.doSet)
        
        arg = processing.execute(decoding=idecoding, **keyargs)
        assert isinstance(arg.decoding, Decoding), 'Invalid decoding %s' % arg.decoding
        
        if arg.decoding.doDecode:
            decoding.doDecode = self.createDecode(arg.decoding.doDecode, decoding)
        else:
            log.error('Cannot decode list item %s', decoding.type.itemType)
            raise Abort(decoding)

    # ----------------------------------------------------------------
    
    def createSetItem(self, getter, setter):
        '''
        Create the do set for the item.
        '''
        assert isinstance(getter, IDo), 'Invalid getter %s' % getter
        assert isinstance(setter, IDo), 'Invalid setter %s' % setter
        def doSet(target, value):
            '''
            Do set the item value.
            '''
            previous = getter(target)
            if previous is None: setter(target, [value])
            else:
                assert isinstance(previous, list), 'Invalid previous value %s' % previous
                previous.append(value)
        return doSet
    
    def createDecode(self, decode, decoding):
        '''
        Create the do decode for list.
        '''
        assert isinstance(decode, IDo), 'Invalid decode %s' % decode
        def doDecode(target, value):
            '''
            Do decode the list.
            '''
            if not isinstance(value, list): addFailure(target, decoding, value=value)
            else:
                for item in value: decode(target, item)
        return doDecode
