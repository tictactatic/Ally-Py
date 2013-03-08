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
from ally.core.impl.processor.encoder.model import ModelEncode
from ally.core.impl.processor.encoder.property import PropertyEncode
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
def assemblyPropertyEncode() -> Assembly:
    '''
    The assembly containing the encoders for properties encoding.
    '''
    return Assembly('Encode model property')

@ioc.entity
def collectionEncode() -> Handler:
    b = CollectionEncode()
    b.itemEncodeAssembly = assemblyItemEncode()
    return b

@ioc.entity
def modelEncode() -> Handler:
    b = ModelEncode()
    b.propertyEncodeAssembly = assemblyPropertyEncode()
    return b

@ioc.entity
def propertyEncode() -> Handler: return PropertyEncode()

# --------------------------------------------------------------------

@ioc.before(assemblyEncode)
def updateAssemblyEncode():
    assemblyEncode().add(collectionEncode(), modelEncode())
    
@ioc.before(assemblyItemEncode)
def updateAssemblyItemEncode():
    assemblyItemEncode().add(modelEncode())
    
@ioc.before(assemblyPropertyEncode)
def updateAssemblyPropertyEncode():
    assemblyPropertyEncode().add(propertyEncode())
