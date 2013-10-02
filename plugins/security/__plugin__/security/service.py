'''
Created on Jan 9, 2012

@package: security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for security.
'''
    
from ..plugin.registry import registerService
from .database import binders
from ally.container import support, bind, ioc

# --------------------------------------------------------------------

SERVICES = 'security.api.**.I*Service', 'security.**.api.**.I*Service'

bind.bindToEntities('security.impl.**.*Alchemy', 'security.**.impl.**.*Alchemy', binders=binders)
support.createEntitySetup('security.impl.**.*', 'security.**.impl.**.*')
support.listenToEntities(*SERVICES, listeners=registerService)
support.loadAllEntities(*SERVICES)

# --------------------------------------------------------------------

@ioc.entity
def signaturesRight() -> dict:
    ''' The right signatures that can be injected'''
    return {}
