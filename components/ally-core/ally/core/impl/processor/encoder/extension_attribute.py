'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the extension encoder.
'''

from ally.api.operator.type import TypeExtension
from ally.api.type import typeFor
from ally.container.ioc import injected
from ally.core.spec.transform.encoder import IAttributes, IEncoder, \
    AttributesJoiner
from ally.core.spec.transform.render import IRender
from ally.design.cache import CacheWeak
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Included
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain, Processing
from ally.design.processor.handler import HandlerBranchingProceed
from ally.exception import DevelError

# --------------------------------------------------------------------

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    attributes = defines(IAttributes, doc='''
    @rtype: IAttributes
    The attributes provider from the extension.
    ''')

class CreateProperty(Context):
    '''
    The create property encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The name used to render the property with.
    ''')
    objType = defines(object, doc='''
    @rtype: object
    The type of the property.
    ''')
    # ---------------------------------------------------------------- Required
    encoder = requires(IEncoder)
    
# --------------------------------------------------------------------

@injected
class ExtensionAttributeEncode(HandlerBranchingProceed):
    '''
    Implementation for a handler that provides the extension encoding in attributes.
    '''
    
    propertyEncodeAssembly = Assembly
    # The encode processors to be used for encoding primitive properties.
    
    def __init__(self):
        assert isinstance(self.propertyEncodeAssembly, Assembly), \
        'Invalid property encode assembly %s' % self.propertyEncodeAssembly
        super().__init__(Included(self.propertyEncodeAssembly).using(create=CreateProperty))
        
        self._cache = CacheWeak()
        
    def process(self, propertyProcessing, create:Create, **keyargs):
        '''
        @see: HandlerBranchingProceed.process
        
        Create the extension attributes.
        '''
        assert isinstance(propertyProcessing, Processing), 'Invalid processing %s' % propertyProcessing
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if create.attributes: attributes = create.attributes
        else: attributes = None
        
        cache = self._cache.key(propertyProcessing, attributes)
        if not cache.has: cache.value = AttributesExtension(self.processProperties, propertyProcessing, attributes)
        create.attributes = cache.value
        
    # ----------------------------------------------------------------
    
    def processProperties(self, extensionType, processing):
        '''
        Process the properties encoders.
        '''
        assert isinstance(extensionType, TypeExtension), 'Invalid extension type %s' % extensionType
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        
        cache = self._cache.key(processing, extensionType)
        if not cache.has:
            properties = cache.value = []
            for propType in extensionType.propertyTypes():
                chain = Chain(processing)
                chain.process(create=processing.ctx.create(objType=propType, name=propType.property)).doAll()
                create = chain.arg.create
                assert isinstance(create, CreateProperty), 'Invalid create property %s' % create
                if create.encoder is None: raise DevelError('Cannot encode %s' % propType)
                properties.append((propType.property, create.encoder))
        
        return cache.value

# --------------------------------------------------------------------

class AttributesExtension(AttributesJoiner):
    '''
    Implementation for a @see: IAttributes for extension types.
    '''
    
    def __init__(self, provider, processing, attributes=None):
        '''
        Construct the extension attributes.
        '''
        assert callable(provider), 'Invalid properties provider %s' % provider
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        super().__init__(attributes)
        
        self.provider = provider
        self.processing = processing
        
    def provideIntern(self, obj, support):
        '''
        @see: AttributesJoiner.provideIntern
        '''
        typeExt = typeFor(obj)
        if not typeExt or not isinstance(typeExt, TypeExtension): return  # Is not an extension object, nothing to do
        
        render = RenderAttributes()
        for name, encoder in self.provider(typeExt, self.processing):
            assert isinstance(encoder, IEncoder), 'Invalid property encoder %s' % encoder
            objValue = getattr(obj, name)
            if objValue is None: continue
            encoder.render(objValue, render, support)
        return render.attributes

class RenderAttributes(IRender):
    '''
    Implementation for @see: IRender used for attributes.
    '''
    __slots__ = ('attributes',)
    
    def __init__(self):
        '''
        Construct the render attributes.
        '''
        self.attributes = {}
        
    def property(self, name, value):
        '''
        @see: IRender.property
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(value, str), 'Invalid value %s' % value
        
        self.attributes[name] = value

    def beginObject(self, name, attributes=None):
        '''
        @see: IRender.beginObject
        '''
        raise NotImplementedError('Not available for attributes rendering')

    def beginCollection(self, name, attributes=None):
        '''
        @see: IRender.beginCollection
        '''
        raise NotImplementedError('Not available for attributes rendering')

    def end(self):
        '''
        @see: IRender.end
        '''
        raise NotImplementedError('Not available for attributes rendering')
