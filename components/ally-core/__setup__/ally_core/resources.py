'''
Created on Nov 24, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the resources.
'''

from .assembler import assemblers
from ally.container import ioc
from ally.core.impl.resources_management import ResourcesRegister
from ally.core.spec.resources import IResourcesRegister, Node
from ally.core.impl.node import NodeRoot

# --------------------------------------------------------------------
# Creating the resource manager

@ioc.entity
def resourcesRoot() -> Node: return NodeRoot()

@ioc.entity
def resourcesRegister() -> IResourcesRegister:
    b = ResourcesRegister(); yield b
    b.root = resourcesRoot()
    b.assemblers = assemblers()
