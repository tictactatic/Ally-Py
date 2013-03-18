'''
Created on Mar 18, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the resource paths encoding.
'''

from ally.api.type import Iter, Type
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer, Path
from ally.core.spec.transform.encoder import IEncoder
from ally.core.spec.transform.render import IRender
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IEncoderPath
from ally.support.core.util_resources import pathLongName
from collections import Iterable

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder for the resources.
    ''')
    # ---------------------------------------------------------------- Required
    objType = requires(object)

class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
    encoderPath = requires(IEncoderPath)
    
# --------------------------------------------------------------------

@injected
class ResourcesEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the resources encoding.
    '''
    
    nameResources = 'Resources'
    # The name used for resources paths.
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameResources, str), 'Invalid resources name %s' % self.nameResources
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(support=Support)
        
        self._encoder = EncoderResources(self.nameResources, self.nameRef)
        
    def process(self, create:Create, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Create the collection encoder.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, Iter): return
        # The type is not for a collection, nothing to do, just move along
        assert isinstance(create.objType, Iter)
        assert isinstance(create.objType.itemType, Type)
        if not create.objType.itemType.isOf(Path): return
        # The type is not for a path, nothing to do, just move along
        
        create.encoder = self._encoder

# --------------------------------------------------------------------

class EncoderResources(IEncoder):
    '''
    Implementation for a @see: IEncoder for resources.
    '''
    
    def __init__(self, nameResources, nameRef):
        '''
        Construct the resources encoder.
        '''
        assert isinstance(nameResources, str), 'Invalid resources name %s' % nameResources
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        
        self.nameResources = nameResources
        self.nameRef = nameRef
        
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(obj, Iterable), 'Invalid collection object %s' % obj
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert isinstance(support.encoderPath, IEncoderPath), 'Invalid path encoder %s' % support.encoderPath
        
        render.collectionStart(support.normalizer.normalize(self.nameResources))
        for path in obj:
            attributes = {support.normalizer.normalize(self.nameRef): support.encoderPath.encode(path)}
            render.objectStart(support.normalizer.normalize(pathLongName(path)), attributes)
            render.objectEnd()
        render.collectionEnd()
