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

# --------------------------------------------------------------------

SERVICES = 'assemblage.api.**.I*Service'

support.createEntitySetup('assemblage.impl.**.*')
support.listenToEntities(SERVICES, listeners=registerService)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

@ioc.entity
def assemblagesAssembly() -> Assembly:
    ''' Assembly used for getting the assemblages'''
    return Assembly('Assemblages')
