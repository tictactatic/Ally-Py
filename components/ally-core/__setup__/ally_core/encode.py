'''
Created on Mar 8, 2013

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the encode processors.
'''

from ally.container import ioc
from ally.core.impl.processor.encoder.collection import CollectionEncode
from ally.core.impl.processor.encoder.extension_attribute import \
    ExtensionAttributeEncode
from ally.core.impl.processor.encoder.model import ModelEncode
from ally.core.impl.processor.encoder.model_property import ModelPropertyEncode
from ally.core.impl.processor.encoder.property import PropertyEncode
from ally.core.impl.processor.encoder.property_id import PropertyIdEncode
from ally.core.impl.processor.encoder.property_of_model import \
    PropertyOfModelEncode
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

@ioc.entity
def assemblyEncode() -> Assembly:
    '''
    The assembly containing the encoders.
    '''
    return Assembly('Encode')

@ioc.entity
def assemblyItemEncode() -> Assembly:
    '''
    The assembly containing the encoders for items encoding.
    '''
    return Assembly('Encode collection item')

@ioc.entity
def assemblyPropertyPrimitiveEncode() -> Assembly:
    '''
    The assembly containing the encoders for properties encoding.
    '''
    return Assembly('Encode primitive property')

@ioc.entity
def assemblyPropertyModelEncode() -> Assembly:
    '''
    The assembly containing the encoders for properties encoding.
    '''
    return Assembly('Encode property of model')

@ioc.entity
def assemblyPropertyEncode() -> Assembly:
    '''
    The assembly containing the encoders for properties encoding.
    '''
    return Assembly('Encode property')

@ioc.entity
def assemblyModelExtraEncode() -> Assembly:
    '''
    The assembly containing the encoders for extra model data encoding.
    '''
    return Assembly('Encode model extra')

# --------------------------------------------------------------------

@ioc.entity
def collectionEncode() -> Handler:
    b = CollectionEncode()
    b.itemEncodeAssembly = assemblyItemEncode()
    return b

@ioc.entity
def modelEncode() -> Handler:
    b = ModelEncode()
    b.propertyEncodeAssembly = assemblyPropertyEncode()
    b.modelExtraEncodeAssembly = assemblyModelExtraEncode()
    return b

@ioc.entity
def modelPropertyEncode() -> Handler:
    b = ModelPropertyEncode()
    b.propertyEncodeAssembly = assemblyPropertyPrimitiveEncode()
    return b

@ioc.entity
def propertyEncode() -> Handler: return PropertyEncode()

@ioc.entity
def propertyIdEncode() -> Handler: return PropertyIdEncode()

@ioc.entity
def propertyOfModelEncode() -> Handler:
    b = PropertyOfModelEncode()
    b.propertyModelEncodeAssembly = assemblyPropertyModelEncode()
    return b

@ioc.entity
def extensionAttributeEncode() -> Handler:
    b = ExtensionAttributeEncode()
    b.propertyEncodeAssembly = assemblyPropertyPrimitiveEncode()
    return b

# --------------------------------------------------------------------

@ioc.before(assemblyEncode)
def updateAssemblyEncode():
    assemblyEncode().add(extensionAttributeEncode(), collectionEncode(), modelEncode(), modelPropertyEncode())
    
@ioc.before(assemblyItemEncode)
def updateAssemblyItemEncode():
    assemblyItemEncode().add(modelEncode(), modelPropertyEncode())
    
@ioc.before(assemblyPropertyModelEncode)
def updateAssemblyPropertyModelEncode():
    assemblyPropertyModelEncode().add(modelPropertyEncode())

@ioc.before(assemblyPropertyPrimitiveEncode)
def updateAssemblyPropertyPrimitiveEncode():
    assemblyPropertyPrimitiveEncode().add(propertyIdEncode(), propertyEncode())
    
@ioc.before(assemblyPropertyEncode)
def updateAssemblyPropertyEncode():
    assemblyPropertyEncode().add(propertyOfModelEncode(), assemblyPropertyPrimitiveEncode())
