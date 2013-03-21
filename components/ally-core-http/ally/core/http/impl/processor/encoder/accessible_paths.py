'''
Created on Mar 18, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the accessible paths for a model.
'''

from ally.container.ioc import injected
from ally.core.http.spec.transform.flags import ATTRIBUTE_REFERENCE
from ally.core.spec.resources import Normalizer
from ally.core.spec.transform.encoder import IEncoder
from ally.core.spec.transform.render import IRender
from ally.core.spec.transform.representation import Attribute, Object
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IEncoderPath

# --------------------------------------------------------------------
    
class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder for the accessible paths.
    ''')
    
class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Optional
    encoderPath = optional(IEncoderPath)
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
    pathsAccesible = requires(dict)
    
# --------------------------------------------------------------------

@injected
class AccessiblePathEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the accessible paths encoding.
    '''
    
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(support=Support)
        
        self._encoder = EncoderAccessiblePath(self.nameRef)
        
    def process(self, create:Create, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Create the accesible path encoder.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
            
        create.encoder = self._encoder

# --------------------------------------------------------------------

class EncoderAccessiblePath(IEncoder):
    '''
    Implementation for a @see: IEncoder for model paths.
    '''
    
    def __init__(self, nameRef):
        '''
        Construct the model paths encoder.
        '''
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        
        self.nameRef = nameRef
    
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        if not support.pathsAccesible: return  # No accessible paths.
        
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert isinstance(support.pathsAccesible, dict), 'Invalid accessible paths %s' % support.pathsAccesible
        assert Support.encoderPath in support, 'No path encoder available in %s' % support
        assert isinstance(support.encoderPath, IEncoderPath), 'Invalid path encoder %s' % support.encoderPath
        
        for name, path in support.pathsAccesible.items():
            attributes = {support.normalizer.normalize(self.nameRef): support.encoderPath.encode(path)}
            render.beginObject(support.normalizer.normalize(name), attributes).end()

    def represent(self, support, obj=None):
        '''
        @see: IEncoder.represent
        '''
        assert isinstance(support, Support), 'Invalid support %s' % support
        if not support.pathsAccesible: return  # No accessible paths.
        
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert isinstance(support.pathsAccesible, dict), 'Invalid accessible paths %s' % support.pathsAccesible
        assert isinstance(obj, Object), 'Invalid representation object to push in %s' % obj
        
        for name in support.pathsAccesible:
            attributes = {support.normalizer.normalize(self.nameRef): Attribute(ATTRIBUTE_REFERENCE)}
            obj.properties.append(Object(support.normalizer.normalize(name), attributes=attributes))
