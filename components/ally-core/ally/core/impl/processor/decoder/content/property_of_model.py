'''
Created on Jul 24, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the properties of model decoding.
'''

from ally.api.operator.type import TypeProperty, TypeModel
from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.impl.processor.base import FailureTarget, addFailure
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Abort
from ally.design.processor.handler import HandlerBranching
from ally.support.util_context import listing
from ally.support.util_spec import IDo
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Decoding(Context):
    '''
    The model decoding context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The decoder name.
    ''')
    parent = defines(Context, doc='''
    @rtype: Context
    The parent decoding that this decoding is based on.
    ''')
    property = defines(TypeProperty, doc='''
    @rtype: TypeProperty
    The property that represents the decoding.
    ''')
    children = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The decoding children indexed by the decoding name.
    ''')
    doDecode = defines(IDo, doc='''
    @rtype: callable(target, value)
    Decodes the value into the provided target.
    @param target: Context
        Target context object used for decoding.
    @param value: object
        The value to be decoded.
    ''')
    # ---------------------------------------------------------------- Required
    type = requires(Type)
    doSet = requires(IDo)
    doGet = requires(IDo)
    
# --------------------------------------------------------------------

@injected
class PropertyOfModelDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the properties of model values decoding.
    '''
    
    decodePropertyAssembly = Assembly
    # The decode processors to be used for decoding the property.
    
    def __init__(self):
        assert isinstance(self.decodePropertyAssembly, Assembly), \
        'Invalid property decode assembly %s' % self.decodePropertyAssembly
        super().__init__(Branch(self.decodePropertyAssembly).included(), Target=FailureTarget)
        
    def process(self, chain, processing, decoding:Decoding, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the property of model decode.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if not isinstance(decoding.type, TypeProperty): return
        # If the type is not property just move along.
        assert isinstance(decoding.type, TypeProperty)
        if not isinstance(decoding.type.parent, TypeModel): return 
        # If the parent is not model just move along.
        
        pdecoding = decoding.__class__()
        assert isinstance(pdecoding, Decoding), 'Invalid decoding %s' % pdecoding
        
        pdecoding.name = decoding.type.name
        pdecoding.parent = decoding
        pdecoding.property = decoding.type
        pdecoding.type = decoding.type.type
        pdecoding.doSet = decoding.doSet
        pdecoding.doGet = decoding.doGet
        
        arg = processing.execute(decoding=pdecoding, **keyargs)
        assert isinstance(arg.decoding, Decoding), 'Invalid decoding %s' % arg.decoding
        if not arg.decoding.doDecode:
            log.error('Cannot decode property \'%s\' of %s',
                      '.'.join(reversed(listing(arg.decoding, Decoding.parent, Decoding.name))),
                      arg.decoding.type)
            raise Abort(arg.decoding)
        
        if decoding.children is None:  decoding.children = {}
        decoding.children[arg.decoding.name] = arg.decoding
        decoding.doDecode = self.createDecode(decoding, arg.decoding.doDecode)
    
    # ----------------------------------------------------------------

    def createDecode(self, decoding, decode):
        '''
        Create the property of model do decode.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(decoding.children, dict), 'Invalid decoding children %s' % decoding.children
        assert isinstance(decode, IDo), 'Invalid decode %s' % decode
        def doDecode(target, value):
            '''
            Do decode the property of model.
            '''
            if not isinstance(value, dict): return decode(target, value)
            assert isinstance(decoding, Decoding)
            
            for pname, pvalue in value.items():
                cdecoding = decoding.children.get(pname)
                if not cdecoding:
                    addFailure(target, decoding, value=pname)
                    continue
                assert isinstance(cdecoding, Decoding), 'Invalid decoding %s' % cdecoding
                assert isinstance(cdecoding.doDecode, IDo), 'Invalid decode %s' % cdecoding.doDecode
                cdecoding.doDecode(target, pvalue)
        return doDecode
