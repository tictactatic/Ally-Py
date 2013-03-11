'''
Created on Mar 8, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the encode processors.
'''

from ..ally_core.encode import updateAssemblyEncode, assemblyEncode, \
    modelPropertyEncode, assemblyItemEncode, updateAssemblyItemEncode, \
    updateAssemblyPropertyModelEncode, assemblyPropertyModelEncode
from ally.container import ioc
from ally.core.http.impl.processor.encoder.path_attribute import PathEncode
from ally.design.processor.handler import Handler

# --------------------------------------------------------------------

@ioc.entity
def pathEncode() -> Handler: return PathEncode()

# --------------------------------------------------------------------

@ioc.after(updateAssemblyEncode)
def updateAssemblyEncodeWithPath():
    assemblyEncode().add(pathEncode(), before=modelPropertyEncode())
    
@ioc.after(updateAssemblyItemEncode)
def updateAssemblyItemEncodeWithPath():
    assemblyItemEncode().add(pathEncode(), before=modelPropertyEncode())

@ioc.after(updateAssemblyPropertyModelEncode)
def updateAssemblyPropertyModelEncodeWithPath():
    assemblyPropertyModelEncode().add(pathEncode(), before=modelPropertyEncode())
