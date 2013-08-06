'''
Created on Jul 15, 2013

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides aid contexts and support functions that are generally used.
'''

from ally.api.type import Type
from ally.core.spec.transform import ITransfrom
from ally.design.processor.attribute import requires, defines, optional, \
    definesIf
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerProcessor
from ally.design.processor.resolvers import resolverFor
from ally.design.processor.spec import IResolver
from ally.design.processor.assembly import Assembly

# --------------------------------------------------------------------
# The create contexts.

class RequestEncoder(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    objType = definesIf(Type, doc='''
    @rtype: Type
    The type that is the target of the encoder create.
    ''')
    # ---------------------------------------------------------------- Required
    encoder = requires(ITransfrom)
    
class RequestEncoderNamed(RequestEncoder):
    '''
    The request create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    name = defines(str, doc='''
    @rtype: string
    The name used to render with.
    ''')
    
class DefineEncoder(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(ITransfrom, doc='''
    @rtype: ITransfrom
    The encoder to be used for rendering objects.
    ''')
    # ---------------------------------------------------------------- Optional
    name = optional(str)
    specifiers = optional(list)
    # ---------------------------------------------------------------- Required
    objType = requires(Type)

# --------------------------------------------------------------------

def createEncoder(processing, objType, **keyargs):
    '''
    Creates the encoder for the provided type by using the processing.
    
    @param processing: Processing
        The processing used for creating the encoder.
    @param objType: Type
        The object type to create the encoder for.
    @param keyargs: key arguments
        Additional parameters to be passed on to the processing.
    @return: ITransform|None
        The created encoder or None if no encoder has been created by processing.
    '''
    assert isinstance(processing, Processing), 'Invalid processing %s' % processing
    assert isinstance(objType, Type), 'Invalid object type %s' % objType
    
    create = processing.ctx.create()
    assert isinstance(create, RequestEncoder), 'Invalid create %s' % create
    if RequestEncoder.objType in create: create.objType = objType
    
    arg = processing.executeWithAll(create=create, **keyargs)
    assert isinstance(arg.create, RequestEncoder), 'Invalid create %s' % arg.create
    return arg.create.encoder

def createEncoderNamed(processing, name, objType, **keyargs):
    '''
    Creates the encoder for the provided type by using the processing.
    
    @param processing: Processing
        The processing used for creating the encoder.
    @param name: string
        The name used to render with.
    @param objType: Type
        The object type to create the encoder for.
    @param keyargs: key arguments
        Additional parameters to be passed on to the processing.
    @return: ITransform|None
        The created encoder or None if no encoder has been created by processing.
    '''
    assert isinstance(processing, Processing), 'Invalid processing %s' % processing
    assert isinstance(objType, Type), 'Invalid object type %s' % objType
    
    create = processing.ctx.create(name=name)
    assert isinstance(create, RequestEncoderNamed), 'Invalid create %s' % create
    if RequestEncoderNamed.objType in create: create.objType = objType
    
    arg = processing.executeWithAll(create=create, **keyargs)
    assert isinstance(arg.create, RequestEncoderNamed), 'Invalid create %s' % arg.create
    return arg.create.encoder

def encoderSpecifiers(context):
    '''
    Provides the specifiers for the provided context.
    
    @param context: Context
        The context with the specifiers to fetch from.
    @return: list|None
        The list of specifiers or None if there is no specifier list available.
    '''
    if DefineEncoder.specifiers in context and context.specifiers: return context.specifiers
    
def encoderName(context, default=None):
    '''
    Provides the name for the provided context.
    
    @param context: Context
        The context with the name to fetch from.
    @return: string|default
        The found name or the provided default value.
    '''
    if DefineEncoder.name in context and context.name: return context.name
    return default

# --------------------------------------------------------------------

class DefineExport(Context):
    '''
    The define export context.
    '''
    # ---------------------------------------------------------------- Defined
    Support = defines(IResolver, doc='''
    @rtype: IResolver
    The support resolver.
    ''')

class RequestExport(Context):
    '''
    The request export context.
    '''
    # ---------------------------------------------------------------- Required
    Support = requires(IResolver)

class ExportingSupport(HandlerProcessor):
    '''
    Implementation for a handler that provides the support exporting.
    '''
    
    def __init__(self, Support):
        super().__init__()
        self.Support = resolverFor(Support)
        
    def process(self, chain, export:DefineExport, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process the export.
        '''
        assert isinstance(export, DefineExport), 'Invalid export %s' % export
        
        if export.Support:
            assert isinstance(export.Support, IResolver), 'Invalid support %s' % export.Support
            export.Support = export.Support.solve(self.Support)
        else: export.Support = self.Support

def importSupport(exportAssembly):
    '''
    Imports the support context.
    
    @param exportAssembly: Assembly
        The assembly containing the exported supports.
    @return: IResolver
        The support resolver.
    '''
    assert isinstance(exportAssembly, Assembly), 'Invalid export assembly %s' % exportAssembly
    processing = exportAssembly.create(export=RequestExport)
    assert isinstance(processing, Processing), 'Invalid processing %s' % processing
    arg = processing.executeWithAll()
    assert isinstance(arg.export, RequestExport), 'Invalid export %s' % arg.export
    assert isinstance(arg.export.Support, IResolver), 'Invalid resolver %s' % arg.export.Support
    return arg.export.Support
