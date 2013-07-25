'''
Created on Jun 16, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the decode processors.
'''

from ..ally_core.decode import assemblyDecode, updateAssemblyDecode, \
    primitiveDecode
from ally.container import ioc
from ally.core.http.impl.processor.decoder.create_parameter import \
    CreateParameterDecode
from ally.core.http.impl.processor.decoder.create_parameter_order import \
    CreateParameterOrderDecode
from ally.core.http.impl.processor.decoder.parameter.explode import \
    ExplodeDecode
from ally.core.http.impl.processor.decoder.parameter.index import \
    IndexParameterDecode
from ally.core.http.impl.processor.decoder.parameter.option import OptionDecode
from ally.core.http.impl.processor.decoder.parameter.order import OrderDecode
from ally.core.http.impl.processor.decoder.parameter.query import QueryDecode
from ally.core.impl.processor.decoder.general.list_decode import ListDecode
from ally.design.processor.assembly import Assembly
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
def assemblyDecodeItem() -> Assembly:
    '''
    The assembly containing the decoders for list items.
    '''
    return Assembly('Decode parameter list item')

# --------------------------------------------------------------------

@ioc.entity
def createParameterDecode() -> Handler:
    b = CreateParameterDecode()
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
    b.listAssembly = assemblyDecodeItem()
    return b

@ioc.entity
def explodeDecode() -> Handler: return ExplodeDecode()

@ioc.entity
def indexParameterDecode() -> Handler:
    b = IndexParameterDecode()
    b.category = CATEGORY_PARAMETER
    return b

# --------------------------------------------------------------------

@ioc.before(assemblyDecodeItem)
def updateAssemblyDecodeItem():
    assemblyDecodeItem().add(primitiveDecode())
    
@ioc.before(assemblyDecodeQuery)
def updateAssemblyDecodeQuery():
    assemblyDecodeQuery().add(orderDecode(), primitiveDecode(), listDecode(), indexParameterDecode(), explodeDecode())
    
@ioc.before(assemblyDecodeParameter)
def updateAssemblyDecodeParameter():
    assemblyDecodeParameter().add(optionDecode(), queryDecode(), orderDecode(), primitiveDecode(), listDecode(),
                                  indexParameterDecode(), explodeDecode())
    
@ioc.before(assemblyDecodeOrder)
def updateAssemblyDecodeOrder():
    assemblyDecodeOrder().add(primitiveDecode(), listDecode(), indexParameterDecode(), explodeDecode())
    
@ioc.after(updateAssemblyDecode)
def updateAssemblyDecodeForParameters():
    assemblyDecode().add(createParameterDecode(), createParameterOrderDecode())
