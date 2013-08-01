'''
Created on Jun 16, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the decode processors.
'''

from ..ally_core.decode import assemblyDecode, updateAssemblyDecode, \
    primitiveDecode, definitionIndex, markSolved, updateAssemblyDecodeModel, \
    assemblyDecodeModel, propertyOfModelDecode
from ally.container import ioc
from ally.core.http.impl.processor.decoder.create_parameter import \
    CreateParameterHandler
from ally.core.http.impl.processor.decoder.create_parameter_order import \
    CreateParameterOrderDecode
from ally.core.http.impl.processor.decoder.create_path import CreatePathHandler
from ally.core.http.impl.processor.decoder.parameter.definition_paramter import \
    DefinitionParameterHandler
from ally.core.http.impl.processor.decoder.parameter.index import \
    IndexParameterHandler
from ally.core.http.impl.processor.decoder.parameter.option import OptionDecode
from ally.core.http.impl.processor.decoder.parameter.order import OrderDecode
from ally.core.http.impl.processor.decoder.parameter.query import QueryDecode
from ally.core.http.impl.processor.decoder.path.injected import \
    InjectedPathDecode
from ally.core.impl.processor.decoder.general.definition_create import \
    DefinitionCreateHandler
from ally.core.impl.processor.decoder.general.explode import ExplodeDecode
from ally.core.impl.processor.decoder.general.list_decode import ListDecode
from ally.design.processor.assembly import Assembly
from ally.design.processor.export import Publish
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

CATEGORY_PARAMETER = 'parameter'
# The name of the parameters category.

# --------------------------------------------------------------------

@ioc.entity
def assemblyDecodeParameter() -> Assembly:
    '''
    The assembly containing the decoders for parameters.
    '''
    return Assembly('Decode parameter')

@ioc.entity
def assemblyDecodeQuery() -> Assembly:
    '''
    The assembly containing the decoders for query parameters.
    '''
    return Assembly('Decode parameter query')

@ioc.entity
def assemblyDecodeOrder() -> Assembly:
    '''
    The assembly containing the decoders for order parameters.
    '''
    return Assembly('Decode parameter order')

@ioc.entity
def assemblyDecodeListItem() -> Assembly:
    '''
    The assembly containing the decoders for list items.
    '''
    return Assembly('Decode parameter list item')

# --------------------------------------------------------------------

@ioc.entity
def assemblyDecodePath() -> Assembly:
    '''
    The assembly containing the decoders for path items.
    '''
    return Assembly('Decode path')

# --------------------------------------------------------------------

@ioc.entity
def createParameter() -> Handler:
    b = CreateParameterHandler()
    b.decodeParameterAssembly = assemblyDecodeParameter()
    return b

@ioc.entity
def createParameterOrderDecode() -> Handler:
    b = CreateParameterOrderDecode()
    b.decodeOrderAssembly = assemblyDecodeOrder()
    return b

@ioc.entity
def queryDecode() -> Handler:
    b = QueryDecode()
    b.decodeQueryAssembly = assemblyDecodeQuery()
    return b

@ioc.entity
def orderDecode() -> Handler: return OrderDecode()

@ioc.entity
def optionDecode() -> Handler: return OptionDecode()

@ioc.entity
def listDecode() -> Handler:
    b = ListDecode()
    b.listItemAssembly = assemblyDecodeListItem()
    return b

@ioc.entity
def explodeDecode() -> Handler: return ExplodeDecode()

# --------------------------------------------------------------------

@ioc.entity
def indexParameter() -> Handler: return IndexParameterHandler()

@ioc.entity
def definitionCreate() -> Handler:
    b = DefinitionCreateHandler()
    b.category = CATEGORY_PARAMETER
    return b

@ioc.entity
def definitionParameter() -> Handler: return DefinitionParameterHandler()

@ioc.entity
def publishParameter() -> Publish: return Publish()

# --------------------------------------------------------------------

@ioc.entity
def createPath() -> Handler:
    b = CreatePathHandler()
    b.decodePathAssembly = assemblyDecodePath()
    return b

@ioc.entity
def injectedPathDecode() -> Handler: return InjectedPathDecode()

@ioc.entity
def publishPath() -> Publish: return Publish()

# --------------------------------------------------------------------

@ioc.before(assemblyDecodeListItem)
def updateAssemblyDecodeItem():
    assemblyDecodeListItem().add(primitiveDecode())
    
@ioc.before(assemblyDecodeQuery)
def updateAssemblyDecodeQuery():
    assemblyDecodeQuery().add(orderDecode(), primitiveDecode(), listDecode(), definitionCreate(), explodeDecode(),
                              indexParameter(), definitionParameter(), definitionIndex(), markSolved())
    
@ioc.before(assemblyDecodeParameter)
def updateAssemblyDecodeParameter():
    assemblyDecodeParameter().add(optionDecode(), queryDecode(), orderDecode(), primitiveDecode(), listDecode(),
                                  definitionCreate(), explodeDecode(), indexParameter(), definitionParameter(),
                                  definitionIndex(), markSolved(), publishParameter())
    
@ioc.before(assemblyDecodeOrder)
def updateAssemblyDecodeOrder():
    assemblyDecodeOrder().add(primitiveDecode(), listDecode(), definitionCreate(), explodeDecode(), indexParameter(),
                              definitionParameter(), definitionIndex(), publishParameter())
    
# --------------------------------------------------------------------

@ioc.before(assemblyDecodePath)
def updateAssemblyDecodePath():
    assemblyDecodePath().add(primitiveDecode(), publishPath())
    
@ioc.after(updateAssemblyDecodeModel)
def updateAssemblyDecodeModelForPath():
    assemblyDecodeModel().add(injectedPathDecode(), after=propertyOfModelDecode())

# --------------------------------------------------------------------

@ioc.after(updateAssemblyDecode)
def updateAssemblyDecodeForParameters():
    assemblyDecode().add(createParameter(), createParameterOrderDecode(), createPath())
