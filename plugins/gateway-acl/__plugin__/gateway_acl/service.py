'''
Created on Jan 9, 2012

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for acl gateway.
'''
    
from __setup__.ally_core.resources import injectorAssembly, assemblyAssembler, \
    processMethod
from __setup__.ally_core_http.resources import \
    updateAssemblyAssemblerForHTTPCore
from ally.container import ioc, support
from ally.design.processor.assembly import Assembly

# --------------------------------------------------------------------

# The assembler processors
processFilter = indexAccess = support.notCreated  # Just to avoid errors

# The management processors
processGroup = alterMethod = alterFilter = getAccess = getMethod = getFilter = support.notCreated  # Just to avoid errors

support.createEntitySetup('gateway.core.acl.impl.**.*')

# --------------------------------------------------------------------

@ioc.entity
def assemblyACLManagement() -> Assembly:
    ''' The assembly used for ACL management'''
    return Assembly('ACL management')

# --------------------------------------------------------------------

@ioc.before(assemblyACLManagement)
def updateAssemblyACLManagement():
    assemblyACLManagement().add(injectorAssembly(), processGroup(), alterMethod(), alterFilter(),
                                getAccess(), getMethod(), getFilter())
        
@ioc.after(updateAssemblyAssemblerForHTTPCore)
def updateAssemblyAssemblerForFilter():
    assemblyAssembler().add(processFilter(), before=processMethod())
    assemblyAssembler().add(indexAccess())
