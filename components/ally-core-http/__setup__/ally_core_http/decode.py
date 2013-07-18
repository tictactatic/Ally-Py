'''
Created on Jun 16, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the decode processors.
'''

from ally.container import ioc
from ally.core.http.impl.processor.decoder.parameter.explode import \
    ExplodeDecode
from ally.core.http.impl.processor.decoder.parameter.option import OptionDecode
from ally.core.http.impl.processor.decoder.parameter.order import OrderDecode
from ally.core.http.impl.processor.decoder.parameter.primitive import \
    PrimitiveDecode
from ally.core.http.impl.processor.decoder.parameter.query import QueryDecode
from ally.core.impl.processor.decoder.decode_create import DecodeCreateHandler
from ally.core.impl.processor.decoder.list_decode import ListDecode
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

@ioc.entity
def assemblyDecodeParameters() -> Assembly:
    '''
    The assembly containing the decoders for parameters.
    '''
    return Assembly('Decode parameters')

@ioc.entity
def assemblyDecodePrimitive() -> Assembly:
    '''
    The assembly containing the decoders for primitives parameters.
    '''
    return Assembly('Decode parameters primitive')

@ioc.entity
def assemblyDecodeItem() -> Assembly:
    '''
    The assembly containing the decoders for item parameters.
    '''
    return Assembly('Decode parameters item')

# --------------------------------------------------------------------

@ioc.entity
def queryDecode() -> Handler: return QueryDecode()

@ioc.entity
def orderDecode() -> Handler: return OrderDecode()

@ioc.entity
def decodeCreatePrimitives() -> Handler:
    b = DecodeCreateHandler()
    b.decodeAssembly = assemblyDecodePrimitive()
    return b

@ioc.entity
def optionDecode() -> Handler: return OptionDecode()

@ioc.entity
def listDecode() -> Handler:
    b = ListDecode()
    b.listAssembly = assemblyDecodeItem()
    return b

@ioc.entity
def decodePrimitive() -> Handler: return PrimitiveDecode()

@ioc.entity
def explodeDecode() -> Handler: return ExplodeDecode()

# --------------------------------------------------------------------

@ioc.before(assemblyDecodeItem)
def updateAssemblyDecodeItem():
    assemblyDecodeItem().add(decodePrimitive())
    
@ioc.before(assemblyDecodePrimitive)
def updateAssemblyDecodePrimitive():
    assemblyDecodePrimitive().add(optionDecode(), listDecode(), decodePrimitive(), explodeDecode())
    
@ioc.before(assemblyDecodeParameters)
def updateAssemblyDecodeParameters():
    assemblyDecodeParameters().add(queryDecode(), orderDecode(), decodeCreatePrimitives())
