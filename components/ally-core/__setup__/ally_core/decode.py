'''
Created on Jun 16, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the decode processors.
'''

from ally.container import ioc
from ally.core.impl.processor.decoder.categorize import CategorizeHandler
from ally.core.impl.processor.decoder.model import ModelDecode
from ally.core.impl.processor.decoder.primitive import PrimitiveDecode
from ally.core.impl.processor.decoder.primitive_list import PrimitiveListDecode
from ally.core.spec.transform.encdec import CATEGORY_CONTENT, SEPARATOR_CONTENT
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler

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

# --------------------------------------------------------------------

@ioc.entity
def categoryContent() -> Handler:
    b = CategorizeHandler()
    b.categoryAssembly = assemblyDecodeContent()
    b.category = CATEGORY_CONTENT
    return b

@ioc.entity
def modelDecode() -> Handler:
    b = ModelDecode()
    b.separator = SEPARATOR_CONTENT
    return b

@ioc.entity
def primitiveListDecode() -> Handler: return PrimitiveListDecode()

@ioc.entity
def primitiveDecode() -> Handler: return PrimitiveDecode()

# --------------------------------------------------------------------

@ioc.before(assemblyDecodeContent)
def updateAssemblyDecodeContent():
    assemblyDecodeContent().add(modelDecode(), primitiveDecode(), primitiveListDecode())

@ioc.before(assemblyDecode)
def updateAssemblyDecodeForContent():
    assemblyDecode().add(categoryContent())
