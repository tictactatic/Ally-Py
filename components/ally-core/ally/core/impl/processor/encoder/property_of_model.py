'''
Created on Mar 11, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the properties of model encoder.
'''

from ally.api.operator.type import TypeModelProperty, TypeModel
from ally.container.ioc import injected
from ally.core.spec.transform.encoder import IEncoder
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranchingProceed
from ally.design.processor.branch import Included

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder for the property of model.
    ''')
    # ---------------------------------------------------------------- Required
    name = requires(str)
    objType = requires(object)

# --------------------------------------------------------------------

@injected
class PropertyOfModelEncode(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the encoding for properties that reference another model.
    '''
    
    propertyModelEncodeAssembly = Assembly
    # The encode processors to be used for encoding model properties.
    
    def __init__(self):
        assert isinstance(self.propertyModelEncodeAssembly, Assembly), \
        'Invalid model encode assembly %s' % self.propertyModelEncodeAssembly
        super().__init__(Included(self.propertyModelEncodeAssembly))
        
    def process(self, propertyModelProcessing, create:Create, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Create the property of model encoder.
        '''
        assert isinstance(propertyModelProcessing, Processing), 'Invalid processing %s' % propertyModelProcessing
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypeModelProperty) or not isinstance(create.objType.type, TypeModel): return
        # The type is not for a model property, nothing to do, just move along
            
        modelType = create.objType.type
        
        assert isinstance(create.name, str), 'Invalid property name %s' % create.name
        assert isinstance(modelType, TypeModel)
        assert modelType.hasId(), 'Model type %s, has no id' % modelType

        create.objType = modelType.propertyTypeId()
        Chain(propertyModelProcessing).process(create=create).doAll()
