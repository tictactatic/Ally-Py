'''
Created on Jul 11, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the model decoding.
'''

from ally.api.operator.type import TypeProperty, TypeModel
from ally.api.type import Iter, Boolean, Integer, Number, String, Time, Date, \
    DateTime, Type
from ally.container.ioc import injected
from ally.core.impl.processor.base import FailureTarget, addFailure
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, CONSUMED, Abort
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
class ModelDecode(HandlerBranching):
    '''
    Implementation for a handler that provides the model values decoding.
    '''
    
    decodeModelAssembly = Assembly
    # The decode processors to be used for decoding the model.
    typeOrders = [Boolean, Integer, Number, String, Time, Date, DateTime, Iter]
    # The type that define the order in which the properties should be rendered.
    
    def __init__(self):
        assert isinstance(self.decodeModelAssembly, Assembly), 'Invalid model decode assembly %s' % self.decodeModelAssembly
        assert isinstance(self.typeOrders, list), 'Invalid type orders %s' % self.typeOrders
        super().__init__(Branch(self.decodeModelAssembly).included(), Target=FailureTarget)
        
    def process(self, chain, processing, decoding:Decoding, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the model decode.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        
        if not isinstance(decoding.type, TypeModel): return
        # If the type is not model just move along.
        assert isinstance(decoding.type, TypeModel)
        
        decoding.name = decoding.type.name
        if decoding.children is None:  decoding.children = {}
        for prop in self.sortedTypes(decoding.type):
            assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
            assert isinstance(prop.parent, TypeModel), 'Invalid model property %s' % prop.parent
            
            pdecoding = decoding.__class__()
            assert isinstance(pdecoding, Decoding), 'Invalid decoding %s' % pdecoding
            
            pdecoding.name = prop.name
            pdecoding.parent = decoding
            pdecoding.property = prop
            pdecoding.type = prop.type
            pdecoding.doSet = self.createSet(decoding.doGet, decoding.doSet, prop)
            pdecoding.doGet = self.createGet(decoding.doGet, prop)
            
            consumed, arg = processing.execute(CONSUMED, decoding=pdecoding, **keyargs)
            if not consumed: continue
            assert isinstance(arg.decoding, Decoding), 'Invalid decoding %s' % arg.decoding
            if not arg.decoding.doDecode:
                log.error('Cannot decode property \'%s\' of %s',
                          '.'.join(reversed(listing(arg.decoding, Decoding.parent, Decoding.name))), arg.decoding.type)
                raise Abort(decoding)
            
            decoding.children[pdecoding.name] = arg.decoding
        
        if decoding.children: decoding.doDecode = self.createDecode(decoding)
    
    # ----------------------------------------------------------------
    
    def createGet(self, getter, prop):
        '''
        Create the do get for model property.
        '''
        assert isinstance(getter, IDo), 'Invalid getter %s' % getter
        assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
        def doGet(target):
            '''
            Do get the model property value.
            '''
            assert isinstance(prop, TypeProperty)
            model = getter(target)
            if model is None: return
            return getattr(model, prop.name)
        return doGet
    
    def createSet(self, getter, setter, prop):
        '''
        Create the do set for model property.
        '''
        assert isinstance(getter, IDo), 'Invalid getter %s' % getter
        assert isinstance(setter, IDo), 'Invalid setter %s' % setter
        assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
        def doSet(target, value):
            '''
            Do set the model property value.
            '''
            assert isinstance(prop, TypeProperty)
            assert isinstance(prop.parent, TypeModel), 'Invalid property %s' % prop
            model = getter(target)
            if model is None:
                model = prop.parent.clazz()
                setter(target, model)
            setattr(model, prop.name, value)
        return doSet
    
    def createDecode(self, decoding):
        '''
        Create the model do decode.
        '''
        assert isinstance(decoding, Decoding), 'Invalid decoding %s' % decoding
        assert isinstance(decoding.children, dict), 'Invalid decoding children %s' % decoding.children
        def doDecode(target, value):
            '''
            Do decode the model.
            '''
            assert isinstance(decoding, Decoding)
            
            if not isinstance(value, dict): addFailure(target, decoding, value=value)
            else:
                for pname, pvalue in value.items():
                    cdecoding = decoding.children.get(pname)
                    if not cdecoding:
                        addFailure(target, decoding, value=pname)
                        continue
                    assert isinstance(cdecoding, Decoding), 'Invalid decoding %s' % cdecoding
                    assert isinstance(cdecoding.doDecode, IDo), 'Invalid decode %s' % cdecoding.doDecode
                    cdecoding.doDecode(target, pvalue)
        return doDecode
    
    # --------------------------------------------------------------------
    
    def sortedTypes(self, model):
        '''
        Provides the sorted properties type for the model type.
        '''
        assert isinstance(model, TypeModel), 'Invalid type model %s' % model
        sorted = list(model.properties.values())
        if model.propertyId: sorted.remove(model.propertyId)
        sorted.sort(key=lambda prop: prop.name)
        sorted.sort(key=self.sortKey)
        if model.propertyId: sorted.insert(0, model.propertyId)
        return sorted
    
    def sortKey(self, prop):
        '''
        Provides the sorting key for property types, used in sort functions.
        '''
        assert isinstance(prop, TypeProperty), 'Invalid property type %s' % prop

        for k, ord in enumerate(self.typeOrders):
            if prop.type == ord: break
        return k
