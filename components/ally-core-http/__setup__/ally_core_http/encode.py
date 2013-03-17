'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the encode processors.
'''

from ..ally_core.encode import extensionAttributeEncode, updateAssemblyEncode, \
    assemblyEncode, modelPropertyEncode, assemblyItemEncode, \
    updateAssemblyItemEncode
from ally.container import ioc
from ally.core.http.impl.processor.encoder.model_path import \
    ModelPathAttributeEncode
from ally.core.http.impl.processor.encoder.path_support import PathSupport
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

@ioc.entity
def pathSupport() -> Handler: return PathSupport()

@ioc.entity
def modelPathAttributeEncode() -> Handler: return ModelPathAttributeEncode()

# --------------------------------------------------------------------

@ioc.after(updateAssemblyEncode)
def updateAssemblyEncodeWithPath():
    assemblyEncode().add(pathSupport(), before=extensionAttributeEncode())
    assemblyEncode().add(modelPathAttributeEncode(), before=modelPropertyEncode())
    
@ioc.after(updateAssemblyItemEncode)
def updateAssemblyItemEncodeWithPath():
    assemblyItemEncode().add(modelPathAttributeEncode(), before=modelPropertyEncode())
#TODO: Gabriel: see about this
#@ioc.after(updateAssemblyPropertyModelEncode)
#def updateAssemblyPropertyModelEncodeWithPath():
#    assemblyPropertyModelEncode().add(pathEncode(), before=modelPropertyEncode())
