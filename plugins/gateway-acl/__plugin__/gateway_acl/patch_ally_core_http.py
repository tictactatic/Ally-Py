'''
Created on Feb 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ally core http setup patch.
'''

from ..sql_alchemy.processor import transaction
from ally.container import support, app, ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from __setup__ import ally_core_http  # @UnusedImport
except ImportError: log.info('No ally core http component available, thus no need to register ACL to it')
else:
    from __setup__.ally_core.resources import assemblyAssembler, updateAssemblyAssembler, processMethod
    from __setup__.ally_core_http.resources import conflictResolve

    # The assembler processors
    processFilter = indexFilter = indexAccess = support.notCreated  # Just to avoid errors
    support.createEntitySetup('acl.core.impl.processor.assembler.**.*')
    
    @ioc.after(updateAssemblyAssembler)
    def updateAssemblyAssemblerForFilter():
        assemblyAssembler().add(processFilter(), before=processMethod())
    
    @app.setup(app.DEVEL)
    def updateAssemblyAssemblerForAccess():
        assemblyAssembler().add(indexAccess())
        assemblyAssembler().add(transaction(), indexFilter(), after=conflictResolve())

