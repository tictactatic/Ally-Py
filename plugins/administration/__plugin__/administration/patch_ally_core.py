'''
Created on Aug 31, 2013

@package: administration
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ally core setup patch.
'''

from ..plugin.registry import registerService
from admin.introspection.api.model import IModelService
from ally.container import ioc, support
from ally.design.processor.assembly import Assembly
from ally.design.processor.execution import Processing
from ally.design.processor.handler import Handler
from ally.design.processor.resolvers import resolversFor, solve
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try:
    from __setup__ import ally_core  # @UnusedImport
except ImportError: log.info('No ally core component available, cannot register the introspection')
else:
    from __setup__.ally_core.resources import injectorAssembly
    from admin.introspection.core.impl.processor.index_model import IndexModelHandler
    from admin.introspection.core.impl.processor.introspect import IntrospectHandler
    from admin.introspection.impl.model import ModelService

    support.listenToEntities(IModelService, listeners=registerService)
    support.loadAllEntities(IModelService)

    # --------------------------------------------------------------------
    
    @ioc.entity
    def assemblyIntrospection() -> Assembly:
        ''' The assembly used for generating the introspection models'''
        return Assembly('Introspection')
        
    # ----------------------------------------------------------------
    
    @ioc.entity
    def introspectContexts(): return []
        
    @ioc.entity
    def introspectProcessing() -> Processing:
        assert introspectContexts(), 'At least a set of contexts is required'
        contexts = iter(introspectContexts())
        resolvers = resolversFor(next(contexts))
        for context in contexts: solve(resolvers, context)
        
        return assemblyIntrospection().create(**resolvers)
    
    @ioc.entity
    def introspect() -> Handler: return IntrospectHandler()
    
    @ioc.entity
    def indexModel() -> Handler: return IndexModelHandler()
    
    @ioc.entity
    def modelService() -> IModelService:
        b = ModelService()
        b.processing = introspectProcessing()
        return b

    # ----------------------------------------------------------------
    
    @ioc.before(assemblyIntrospection)
    def updateAssemblyIntrospection():
        assemblyIntrospection().add(injectorAssembly(), introspect(), indexModel())
        
    @ioc.before(introspectContexts)
    def updateIntrospectContexts():
        introspectContexts().append(ModelService.CONTEXTS)
