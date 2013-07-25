'''
Created on Mar 15, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the path support.
'''

from ally.api.operator.type import TypeModel, TypeProperty
from ally.container.ioc import injected
from ally.core.spec.transform import ITransfrom
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create item encoder context.
    '''
    # ---------------------------------------------------------------- Required
    encoder = requires(ITransfrom)

class Support(Context):
    '''
    The support context.
    '''
    # ---------------------------------------------------------------- Defined
    pathValues = defines(dict, doc='''
    @rtype: dictionary{Type: object}
    The values used in constructing the paths.
    ''')
    
# --------------------------------------------------------------------

@injected
class PathUpdaterSupportEncode(HandlerProcessor):
    '''
    Implementation for a handler that provides the models paths update when in a collection.
    '''
    
    def __init__(self):
        super().__init__(Support=Support)
        
    def process(self, chain, create:Create, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Create the update model path encoder.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is None: return 
        # There is no encoder to provide path update for.
        if not isinstance(create.objType, (TypeModel, TypeProperty)): return 
        # The type is not for a path updater, nothing to do, just move along
        
        create.encoder = EncoderPathUpdater(create.encoder, create.objType)
        
# --------------------------------------------------------------------

class EncoderPathUpdater(ITransfrom):
    '''
    Implementation for a @see: ITransfrom that updates the path before encoding .
    '''
    
    def __init__(self, encoder, objType):
        '''
        Construct the path updater.
        '''
        assert isinstance(encoder, ITransfrom), 'Invalid property encoder %s' % encoder
        assert isinstance(objType, (TypeModel, TypeProperty)), 'Invalid object type %s' % objType
        
        self.encoder = encoder
        self.objType = objType
        
    def transform(self, value, target, support):
        '''
        @see: ITransfrom.transform
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        if support.pathValues is None: support.pathValues = {}
        support.pathValues[self.objType] = value
        
        self.encoder.transform(value, target, support)
