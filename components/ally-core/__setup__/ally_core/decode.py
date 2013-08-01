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
from ally.core.impl.processor.decoder.content.definition_content import \
    DefinitionContentHandler
from ally.core.impl.processor.decoder.content.model import ModelDecode
from ally.core.impl.processor.decoder.content.name_children import \
    NameChildrenHandler
from ally.core.impl.processor.decoder.content.property_of_model import \
    PropertyOfModelDecode
from ally.core.impl.processor.decoder.create_content import CreateContentHandler
from ally.core.impl.processor.decoder.general.definition_create import \
    DefinitionCreateHandler
from ally.core.impl.processor.decoder.general.definition_index import \
    DefinitionIndexHandler
from ally.core.impl.processor.decoder.general.dict_decode import DictDecode, \
    DictItemDecode
from ally.core.impl.processor.decoder.general.list_decode import ListDecode
from ally.core.impl.processor.decoder.general.mark_solved import \
    MarkSolvedHandler
from ally.core.impl.processor.decoder.general.primitive import PrimitiveDecode
from ally.core.impl.processor.decoder.option_slice import OptionSliceHandler
from ally.core.impl.processor.render.xml import NAME_LIST_ITEM, NAME_DICT_ENTRY, \
    NAME_DICT_KEY, NAME_DICT_VALUE
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from .parsing_rendering import CATEGORY_CONTENT_OBJECT
from ally.design.processor.export import Publish

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
def assemblyDecodePropertyOfModel() -> Assembly:
    '''
    The assembly containing the decoders for property of model.
    '''
    return Assembly('Decode content property of model')

@ioc.entity
def assemblyDecodeListItem() -> Assembly:
    '''
    The assembly containing the decoders for list items.
    '''
    return Assembly('Decode content list item')

@ioc.entity
def assemblyDecodeDictItem() -> Assembly:
    '''
    The assembly containing the decoders for dictionary items.
    '''
    return Assembly('Decode content dictionary item')

@ioc.entity
def assemblyDecodeDictKey() -> Assembly:
    '''
    The assembly containing the decoders for dictionary key.
    '''
    return Assembly('Decode content dictionary key')

@ioc.entity
def assemblyDecodeDictValue() -> Assembly:
    '''
    The assembly containing the decoders for dictionary value.
    '''
    return Assembly('Decode content dictionary value')

# --------------------------------------------------------------------

@ioc.entity
def optionSlice() -> Handler:
    b = OptionSliceHandler()
    b.defaultLimit = slice_limit_default()
    b.maximumLimit = slice_limit_maximum()
    b.defaultWithTotal = slice_with_total()
    return b

@ioc.entity
def createContent() -> Handler:
    b = CreateContentHandler()
    b.decodeContentAssembly = assemblyDecodeContent()
    return b

@ioc.entity
def modelDecode() -> Handler:
    b = ModelDecode()
    b.decodeModelAssembly = assemblyDecodeModel()
    return b

@ioc.entity
def propertyOfModelDecode() -> Handler:
    b = PropertyOfModelDecode()
    b.decodePropertyAssembly = assemblyDecodePropertyOfModel()
    return b

@ioc.entity
def listDecode() -> Handler:
    b = ListDecode()
    b.listItemAssembly = assemblyDecodeListItem()
    return b

@ioc.entity
def nameListItemChildren() -> Handler:
    b = NameChildrenHandler()
    b.name = NAME_LIST_ITEM
    return b

@ioc.entity
def dictDecode() -> Handler:
    b = DictDecode()
    b.dictItemAssembly = assemblyDecodeDictItem()
    return b

@ioc.entity
def nameDictItemChildren() -> Handler:
    b = NameChildrenHandler()
    b.name = NAME_DICT_ENTRY
    return b

@ioc.entity
def dictItemDecode() -> Handler:
    b = DictItemDecode()
    b.itemKeyAssembly = assemblyDecodeDictKey()
    b.itemValueAssembly = assemblyDecodeDictValue()
    return b

@ioc.entity
def nameDictKeyChildren() -> Handler:
    b = NameChildrenHandler()
    b.name = NAME_DICT_KEY
    return b

@ioc.entity
def nameDictValueChildren() -> Handler:
    b = NameChildrenHandler()
    b.name = NAME_DICT_VALUE
    return b

@ioc.entity
def primitiveDecode() -> Handler: return PrimitiveDecode()

# --------------------------------------------------------------------

@ioc.entity
def markSolved() -> Handler: return MarkSolvedHandler()

@ioc.entity
def definitionIndex() -> Handler: return DefinitionIndexHandler()

@ioc.entity
def definitionXMLCreate() -> Handler:
    b = DefinitionCreateHandler()
    b.category = CATEGORY_CONTENT_XML
    return b

@ioc.entity
def definitionContentXML() -> Handler:
    b = DefinitionContentHandler()
    b.separator = '/'
    return b

@ioc.entity
def definitionObjectCreate() -> Handler:
    b = DefinitionCreateHandler()
    b.category = CATEGORY_CONTENT_OBJECT
    return b

@ioc.entity
def definitionContentObject() -> Handler: return DefinitionContentHandler()

@ioc.entity
def publishContent() -> Publish: return Publish()

# --------------------------------------------------------------------

@ioc.before(assemblyDecodeListItem)
def updateAssemblyDecodeListItem():
    assemblyDecodeListItem().add(nameListItemChildren(), primitiveDecode(), definitionXMLCreate(), definitionContentXML())

@ioc.before(assemblyDecodeDictKey)
def updateAssemblyDecodeDictKey():
    assemblyDecodeDictKey().add(nameDictKeyChildren(), primitiveDecode(), definitionXMLCreate(), definitionContentXML())
    
@ioc.before(assemblyDecodeDictValue)
def updateAssemblyDecodeDictValue():
    assemblyDecodeDictValue().add(nameDictValueChildren(), primitiveDecode(), definitionXMLCreate(), definitionContentXML())
      
@ioc.before(assemblyDecodeDictItem)
def updateAssemblyDecodeDictItem():
    assemblyDecodeDictItem().add(nameDictItemChildren(), dictItemDecode(), definitionXMLCreate(), definitionContentXML())

@ioc.before(assemblyDecodePropertyOfModel)
def updateAssemblyDecodePropertyOfModel():
    assemblyDecodePropertyOfModel().add(primitiveDecode(), definitionXMLCreate(), definitionContentXML())
    
@ioc.before(assemblyDecodeModel)
def updateAssemblyDecodeModel():
    assemblyDecodeModel().add(propertyOfModelDecode(), listDecode(), dictDecode(), primitiveDecode(),
                              definitionXMLCreate(), definitionContentXML(), definitionIndex(),
                              definitionObjectCreate(), definitionContentObject(), definitionIndex())
    
@ioc.before(assemblyDecodeContent)
def updateAssemblyDecodeContent():
    assemblyDecodeContent().add(modelDecode(), markSolved(), publishContent())

@ioc.before(assemblyDecode)
def updateAssemblyDecode():
    assemblyDecode().add(optionSlice(), createContent())
