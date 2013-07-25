'''
Created on Jun 16, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the decode processors.
'''

from .parsing_rendering import CATEGORY_CONTENT_XML
from ally.container import ioc
from ally.core.impl.processor.decoder.content.index import IndexContentDecode
from ally.core.impl.processor.decoder.content.model import ModelDecode
from ally.core.impl.processor.decoder.content.property_of_model import \
    PropertyOfModelDecode
from ally.core.impl.processor.decoder.create_content import CreateContentDecode
from ally.core.impl.processor.decoder.general.list_decode import ListDecode
from ally.core.impl.processor.decoder.general.primitive import PrimitiveDecode
from ally.core.impl.processor.decoder.option_slice import OptionSliceDecode
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.core.impl.processor.render.xml import NAME_LIST_ITEM

# --------------------------------------------------------------------

@ioc.config
def slice_limit_maximum() -> int:
    ''' The maximum imposed slice limit on a collection, if none then no maximum limit will be imposed'''
    return 100

@ioc.config
def slice_limit_default() -> int:
    '''
    The default slice limit on a collection if none is specified, if none then the 'slice_limit_maximum' limit
    will be used as the default one.
    '''
    return 30

@ioc.config
def slice_with_total() -> bool:
    ''' The default value for providing the total count'''
    return True

# --------------------------------------------------------------------

@ioc.entity
def assemblyDecode() -> Assembly:
    '''
    The assembly containing the decoders.
    '''
    return Assembly('Decode')

@ioc.entity
def assemblyDecodeContent() -> Assembly:
    '''
    The assembly containing the decoders for content.
    '''
    return Assembly('Decode content')

@ioc.entity
def assemblyDecodeModel() -> Assembly:
    '''
    The assembly containing the decoders for model.
    '''
    return Assembly('Decode content model')

@ioc.entity
def assemblyDecodeProperty() -> Assembly:
    '''
    The assembly containing the decoders for property.
    '''
    return Assembly('Decode content property')

@ioc.entity
def assemblyDecodeItem() -> Assembly:
    '''
    The assembly containing the decoders for list items.
    '''
    return Assembly('Decode content list item')

# --------------------------------------------------------------------

@ioc.entity
def optionSlice() -> Handler:
    b = OptionSliceDecode()
    b.defaultLimit = slice_limit_default()
    b.maximumLimit = slice_limit_maximum()
    b.defaultWithTotal = slice_with_total()
    return b

@ioc.entity
def createContentDecode() -> Handler:
    b = CreateContentDecode()
    b.decodeContentAssembly = assemblyDecodeContent()
    return b

@ioc.entity
def modelDecode() -> Handler:
    b = ModelDecode()
    b.decodeModelAssembly = assemblyDecodeModel()
    return b

@ioc.entity
def propertyOfModel() -> Handler:
    b = PropertyOfModelDecode()
    b.decodePropertyAssembly = assemblyDecodeProperty()
    return b

@ioc.entity
def listDecode() -> Handler:
    b = ListDecode()
    b.listAssembly = assemblyDecodeItem()
    b.itemName = NAME_LIST_ITEM
    return b

@ioc.entity
def primitiveDecode() -> Handler: return PrimitiveDecode()

# --------------------------------------------------------------------

@ioc.entity
def indexContentXMLDecode() -> Handler:
    b = IndexContentDecode()
    b.separator = '/'
    b.category = CATEGORY_CONTENT_XML
    return b

# --------------------------------------------------------------------

@ioc.before(assemblyDecodeItem)
def updateAssemblyDecodeItem():
    assemblyDecodeItem().add(primitiveDecode(), indexContentXMLDecode())

@ioc.before(assemblyDecodeProperty)
def updateAssemblyDecodeProperty():
    assemblyDecodeProperty().add(listDecode(), primitiveDecode(), indexContentXMLDecode())
    
@ioc.before(assemblyDecodeModel)
def updateAssemblyDecodeModel():
    assemblyDecodeModel().add(propertyOfModel(), listDecode(), primitiveDecode(), indexContentXMLDecode())
    
@ioc.before(assemblyDecodeContent)
def updateAssemblyDecodeContent():
    assemblyDecodeContent().add(modelDecode())

@ioc.before(assemblyDecode)
def updateAssemblyDecode():
    assemblyDecode().add(optionSlice(), createContentDecode())
