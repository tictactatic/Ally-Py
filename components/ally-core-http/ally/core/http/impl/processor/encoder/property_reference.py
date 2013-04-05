'''
Created on Mar 18, 2013

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the reference types encoding.
'''

from ally.api.operator.type import TypeProperty
from ally.api.type import TypeReference
from ally.container.ioc import injected
from ally.core.spec.resources import Normalizer
from ally.core.spec.transform.encoder import IEncoder
from ally.core.spec.transform.render import IRender
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
    The encoder for the reference.
    ''')
    # ---------------------------------------------------------------- Required
    name = requires(str)
    objType = requires(object)

class Support(Context):
    '''
    The encoder support context.
    '''
    # ---------------------------------------------------------------- Optional
    encoderPath = optional(IEncoderPath)
    # ---------------------------------------------------------------- Required
    normalizer = requires(Normalizer)
    
# --------------------------------------------------------------------

@injected
class PropertyReferenceEncode(HandlerProcessorProceed):
    '''
    Implementation for a handler that provides the references types encoding.
    '''
    
    nameRef = 'href'
    # The reference attribute name.
    
    def __init__(self):
        assert isinstance(self.nameRef, str), 'Invalid reference name %s' % self.nameRef
        super().__init__(support=Support)
        
        self._cache = {}
        
    def process(self, create:Create, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Create the collection encoder.
        '''
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, TypeProperty): return 
        # The type is not for a property, nothing to do, just move along
        assert isinstance(create.objType, TypeProperty)
        if not isinstance(create.objType.type, TypeReference): return 
        # The type is not a reference, just move along
        
        assert isinstance(create.name, str), 'Invalid name %s' % create.name
        encoder = self._cache.get(create.name)
        if not encoder: encoder = self._cache[create.name] = EncoderReference(create.name, self.nameRef)
        create.encoder = encoder

# --------------------------------------------------------------------

class EncoderReference(IEncoder):
    '''
    Implementation for a @see: IEncoder for references types.
    '''
    
    def __init__(self, name, nameRef):
        '''
        Construct the reference encoder.
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(nameRef, str), 'Invalid reference name %s' % nameRef
        
        self.name = name
        self.nameRef = nameRef
        
    def render(self, obj, render, support):
        '''
        @see: IEncoder.render
        '''
        assert isinstance(render, IRender), 'Invalid render %s' % render
        assert isinstance(support, Support), 'Invalid support %s' % support
        assert isinstance(support.normalizer, Normalizer), 'Invalid normalizer %s' % support.normalizer
        assert Support.encoderPath in support, 'No path encoder available in %s' % support
        assert isinstance(support.encoderPath, IEncoderPath), 'Invalid path encoder %s' % support.encoderPath
        
        attributes = {support.normalizer.normalize(self.nameRef): support.encoderPath.encode(obj)}
        render.beginObject(support.normalizer.normalize(self.name), attributes).end()
