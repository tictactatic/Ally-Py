'''
Created on Apr 12, 2013

@package: service assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the server patch configuration when used internally with cdm service.
'''

from ..ally_http.server import assemblyServer
from .processor import assemblyForward, updateAssemblyForward, notFoundRouter, \
    server_provide_assemblage, ASSEMBLAGE_INTERNAL, ASSEMBLAGE_EXTERNAL
from ally.container import ioc
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_cdm, ally_core_http
except ImportError: log.info('No CDM service available, no need to patch it')
else: 
    ally_cdm = ally_cdm  # Just to avoid the import warning
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------
    
    from ..ally_cdm.server import server_provide_content, contentRouter, updateAssemblyServerForContent
    
    @ioc.after(updateAssemblyForward)
    def updateAssemblyForwardForContent():
        if server_provide_content() and server_provide_assemblage() in (ASSEMBLAGE_EXTERNAL, ASSEMBLAGE_INTERNAL):
            assemblyForward().add(contentRouter(), before=notFoundRouter())
            
    @ioc.after(updateAssemblyServerForContent)
    def updateAssemblyServerForContentAssemblage():
        if server_provide_content() and server_provide_assemblage() in (ASSEMBLAGE_EXTERNAL, ASSEMBLAGE_INTERNAL):
            assemblyServer().remove(contentRouter())
