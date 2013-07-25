'''
Created on Mar 11, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the properties of model encoder.
'''

from ally.api.operator.type import TypeModel, TypePropertyContainer
from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.spec.transform import ITransfrom
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranching

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(ITransfrom, doc='''
    @rtype: ITransfrom
    The encoder for the property of model.
    ''')
    # ---------------------------------------------------------------- Required
    name = requires(str)
    objType = requires(Type)

# --------------------------------------------------------------------

@injected
class PropertyOfModelEncode(HandlerBranching):
    '''
    Implementation for a handler that provides the encoding for properties that reference another model.
    '''
    
    propertyModelEncodeAssembly = Assembly
    # The encode processors to be used for encoding model properties.
    
    def __init__(self):
        assert isinstance(self.propertyModelEncodeAssembly, Assembly), \
        'Invalid model encode assembly %s' % self.propertyModelEncodeAssembly
        super().__init__(Branch(self.propertyModelEncodeAssembly).included())
        
    def process(self, chain, processing, create:Create, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the property of model encoder.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypePropertyContainer): return
        assert isinstance(create.objType, TypePropertyContainer)
        model = create.objType.container
        if not isinstance(model, TypeModel): return  # The type is not for a model property, nothing to do, just move along
        assert isinstance(model, TypeModel)
        if not model.propertyId: return  # No property id to process.
        
        assert isinstance(create.name, str), 'Invalid property name %s' % create.name
        create.objType = model.propertyId
        chain.branch(processing)
