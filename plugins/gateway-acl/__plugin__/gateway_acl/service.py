'''
Created on Jan 9, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for acl gateway.
'''
    
from __setup__.ally_core.resources import injectorAssembly
from ally.container import ioc, support
from ally.design.processor.assembly import Assembly

# --------------------------------------------------------------------

findAllowInvoker = support.notCreated  # Just to avoid errors

support.createEntitySetup('gateway.core.acl.impl.processor.**.*')

# --------------------------------------------------------------------

@ioc.entity
def assemblyManageAccess() -> Assembly:
    ''' The assembly used for managing the access'''
    return Assembly('ACL manage access')

# --------------------------------------------------------------------

@ioc.before(assemblyManageAccess)
def updateAssemblyManageAccess():
    assemblyManageAccess().add(injectorAssembly(), findAllowInvoker())
