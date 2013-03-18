'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the encode processors.
'''

from ..ally_core.encode import assemblyModelExtraEncode, \
    extensionAttributeEncode, updateAssemblyEncode, assemblyEncode, \
    propertyOfModelEncode, assemblyItemEncode, updateAssemblyItemEncode, \
    assemblyPropertyEncode, updateAssemblyPropertyEncode, modelPropertyEncode, \
    modelEncode
from ally.container import ioc
from ally.core.http.impl.processor.encoder.accessible_paths import \
    AccessiblePathEncode
from ally.core.http.impl.processor.encoder.model_path import \
    ModelPathAttributeEncode
from ally.core.http.impl.processor.encoder.path_support import PathSupport, \
    PathUpdaterSupportEncode
from ally.core.http.impl.processor.encoder.property_of_model_path import \
    PropertyOfModelPathAttributeEncode
from ally.core.http.impl.processor.encoder.property_reference import \
    PropertyReferenceEncode
from ally.core.http.impl.processor.encoder.resources import ResourcesEncode
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

@ioc.entity
def resourcesEncode() -> Handler: return ResourcesEncode()

@ioc.entity
def pathSupport() -> Handler: return PathSupport()

@ioc.entity
def pathUpdaterSupportEncode() -> Handler: return PathUpdaterSupportEncode()

@ioc.entity
def accessiblePathEncode(): return AccessiblePathEncode()

@ioc.entity
def modelPathAttributeEncode() -> Handler: return ModelPathAttributeEncode()

@ioc.entity
def propertyReferenceEncode() -> Handler: return PropertyReferenceEncode()

@ioc.entity
def propertyOfModelPathAttributeEncode() -> Handler: return PropertyOfModelPathAttributeEncode()

# --------------------------------------------------------------------

@ioc.after(updateAssemblyEncode)
def updateAssemblyEncodeWithPath():
    assemblyEncode().add(resourcesEncode(), pathSupport(), before=extensionAttributeEncode())
    assemblyEncode().add(pathUpdaterSupportEncode())

@ioc.after(assemblyModelExtraEncode)
def updateAssemblyModelExtraEncodeWithPath():
    assemblyModelExtraEncode().add(accessiblePathEncode())
   
@ioc.after(updateAssemblyItemEncode)
def updateAssemblyItemEncodeWithPath():
    # assemblyItemEncode().add(modelPathAttributeEncode(), before=modelPropertyEncode())
    # TODO: Gabriel: This is a temporary fix to get the same rendering as before until we refactor the plugins
    # to return only ids.
    assemblyItemEncode().add(modelPathAttributeEncode(), before=modelEncode())
    assemblyItemEncode().add(pathUpdaterSupportEncode())

@ioc.after(updateAssemblyPropertyEncode)
def updateAssemblyPropertyEncodeWithPath():
    assemblyPropertyEncode().add(propertyReferenceEncode(), propertyOfModelPathAttributeEncode(),
                                 before=propertyOfModelEncode())
