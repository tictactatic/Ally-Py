'''
Created on Feb 19, 2013

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ally core http setup patch.
'''

from .service import assemblyAssemblages, updateAssemblyAssemblages, \
    provideMatcherPatterns
from ally.container import ioc, support
from ally.design.processor.handler import Handler, HandlerRenamer
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from __setup__ import ally_core_http
except ImportError: log.info('No ally core http component available, thus cannot provide assemblages support')
else:
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------
    
    from __setup__.ally_core_http.processor import encoderPathResource
    from __setup__.ally_core.processor import normalizerResponse
    from __setup__.ally_core.parsing_rendering import assemblyPattern
    from assemblage.core.impl.processor import resource_data, resource_represent, matcher_data, resource_assemblage
    
    iterateResourceData = provideRepresentation = provideMatchers = assemblagesFromData = support.notCreated  # Just to avoid errors
    support.createEntitySetup(resource_data, resource_represent, matcher_data, resource_assemblage)
    
    # --------------------------------------------------------------------
    
    @ioc.entity
    def encoderPathAssemblage() -> Handler:
        return HandlerRenamer(encoderPathResource(), ('response', 'support'), ('request', 'support'))
    
    @ioc.entity
    def normalizerAssemblage() -> Handler:
        return HandlerRenamer(normalizerResponse(), ('response', 'support'))
        
    # --------------------------------------------------------------------
        
    @ioc.after(updateAssemblyAssemblages)
    def updateAssemblyAssemblagesForCore():
        assemblyAssemblages().add(iterateResourceData(), normalizerAssemblage(), provideRepresentation(), provideMatchers(),
                                  encoderPathAssemblage(), assemblagesFromData(), assemblyPattern(),
                                  before=provideMatcherPatterns())
        
