'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the extension encoder.
'''

from ally.api.operator.type import TypeExtension, TypeProperty
from ally.api.type import typeFor, Iter
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IEncoder, ISpecifier
from ally.core.spec.transform.encdec import IRender
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching
from ally.exception import DevelError

# --------------------------------------------------------------------
    
class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    specifiers = defines(list, doc='''
    @rtype: list[ISpecifier]
    The attributes specifications provider from the extension.
    ''')
    # ---------------------------------------------------------------- Optional
    encoder = optional(IEncoder)
    
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
class ExtensionAttributeEncode(HandlerBranching):
    '''
    Implementation for a handler that provides the extension encoding in attributes.
    '''
    
    propertyEncodeAssembly = Assembly
    # The encode processors to be used for encoding primitive properties.
    
    def __init__(self):
        assert isinstance(self.propertyEncodeAssembly, Assembly), \
        'Invalid property encode assembly %s' % self.propertyEncodeAssembly
        super().__init__(Branch(self.propertyEncodeAssembly).using(create=CreateProperty))
        
    def process(self, chain, propertyProcessing, create:Create, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Create the extension attributes.
        '''
        assert isinstance(propertyProcessing, Processing), 'Invalid processing %s' % propertyProcessing
        assert isinstance(create, Create), 'Invalid create %s' % create
        
        if Create.encoder in create and create.encoder is not None: return 
        # There is already an encoder, nothing to do.
        if not isinstance(create.objType, Iter): return
        # The type is not for a collection so no extension, nothing to do, just move along
        
        if create.specifiers is None: create.specifiers = []
        create.specifiers.append(AttributesExtension(propertyProcessing))

# --------------------------------------------------------------------

class AttributesExtension(ISpecifier):
    '''
    Implementation for a @see: ISpecifier for extension attributes types.
    '''
    
    def __init__(self, processing):
        '''
        Construct the extension attributes.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        
        self.processing = processing
        self.propertiesByType = {}
        
    def populate(self, obj, specifications, support):
        '''
        @see: ISpecifier.populate
        '''
        ext = typeFor(obj)
        if not ext or not isinstance(ext, TypeExtension): return  # Is not an extension object, nothing to do
        assert isinstance(ext, TypeExtension)
        
        if ext not in self.propertiesByType:
            properties = self.propertiesByType[ext] = []
            for name, prop in ext.properties.items():
                assert isinstance(prop, TypeProperty), 'Invalid property %s' % prop
                arg = self.processing.execute(create=self.processing.ctx.create(objType=prop, name=name))
                assert isinstance(arg.create, CreateProperty), 'Invalid create property %s' % arg.create
                if arg.create.encoder is None: raise DevelError('Cannot encode %s' % prop)
                properties.append((name, arg.create.encoder))
        else: properties = self.propertiesByType[ext]
        
        attributes = specifications.get('attributes')
        if attributes is None: attributes = specifications['attributes'] = {}
        render = RenderAttributes(attributes)
        for name, encoder in properties:
            assert isinstance(encoder, IEncoder), 'Invalid property encoder %s' % encoder
            objValue = getattr(obj, name)
            if objValue is None: continue
            encoder.encode(objValue, render, support)

class RenderAttributes(IRender):
    '''
    Implementation for @see: IRender used for attributes.
    '''
    __slots__ = ('attributes',)
    
    def __init__(self, attributes):
        '''
        Construct the renderer attributes.
        
        @param attributes: dictionary{string: string}
            The attributes dictionary to render in.
        '''
        assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
        self.attributes = attributes
        
    def property(self, name, value, **specifications):
        '''
        @see: IRender.property
        '''
        assert isinstance(name, str), 'Invalid name %s' % name
        
        self.attributes[name] = value

    def beginObject(self, name, **specifications):
        '''
        @see: IRender.beginObject
        '''
        raise NotImplementedError('Not available for attributes rendering')

    def beginCollection(self, name, **specifications):
        '''
        @see: IRender.beginCollection
        '''
        raise NotImplementedError('Not available for attributes rendering')

    def end(self):
        '''
        @see: IRender.end
        '''
        raise NotImplementedError('Not available for attributes rendering')
