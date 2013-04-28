'''
Created on Jan 9, 2012

@package: indexing
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for indexing.
'''
    
from ..plugin.registry import registerService
from ally.container import support

# --------------------------------------------------------------------

SERVICES = 'indexing.api.**.I*Service'

support.createEntitySetup('indexing.impl.**.*')
support.listenToEntities(SERVICES, listeners=registerService)
support.loadAllEntities(SERVICES)
