'''
Created on Jan 9, 2012

@package: assemblage
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for assemblage.
'''
    
from ..plugin.registry import registerService
from ally.container import support, ioc
from ally.design.processor.assembly import Assembly
from assemblage.core.impl.processor import matcher, matcher_patterns

# --------------------------------------------------------------------

SERVICES = 'assemblage.api.**.I*Service'

support.createEntitySetup('assemblage.impl.**.*')
support.listenToEntities(SERVICES, listeners=registerService)
support.loadAllEntities(SERVICES)

provideMatcherPatterns = matchersFromData = support.notCreated  # Just to avoid errors
support.createEntitySetup(matcher_patterns, matcher)
    
# --------------------------------------------------------------------

@ioc.entity
def assemblyAssemblages() -> Assembly:
    ''' Assembly used for getting the assemblages'''
    return Assembly('Assemblages')

# --------------------------------------------------------------------

@ioc.before(assemblyAssemblages)
def updateAssemblyAssemblages():
    assemblyAssemblages().add(provideMatcherPatterns(), matchersFromData())
