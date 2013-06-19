'''
Created on Jun 16, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the decode processors.
'''

from ..ally_core.decode import primitiveDecode
from ally.container import ioc
from ally.core.http.impl.processor.decoder.parameter.option import \
    OptionParameterDecode
from ally.core.http.impl.processor.decoder.parameter.query import QueryDecode
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.core.http.impl.processor.decoder.parameter.order import OrderDecode

# --------------------------------------------------------------------

@ioc.entity
def assemblyDecodeParameters() -> Assembly:
    '''
    The assembly containing the decoders for parameters.
    '''
    return Assembly('Decode parameters')

# --------------------------------------------------------------------

@ioc.entity
def optionParameterDecode() -> Handler: return OptionParameterDecode()

@ioc.entity
def queryDecode() -> Handler: return QueryDecode()

@ioc.entity
def orderDecode() -> Handler: return OrderDecode()

# --------------------------------------------------------------------

@ioc.before(assemblyDecodeParameters)
def updateAssemblyDecodeParameters():
    assemblyDecodeParameters().add(queryDecode(), optionParameterDecode(), orderDecode(), primitiveDecode())
    
