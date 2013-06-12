'''
Created on Jun 12, 2013

@package: example
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Martin Saturka

Contains the services for superdesk.
'''

from ..plugin.registry import addService
from .db_example import bindExampleSession, bindExampleValidations
from ally.container import support, bind, ioc
from itertools import chain

# --------------------------------------------------------------------

SERVICES = 'example.*.api.**.I*Service'
@ioc.entity
def binders(): return [bindExampleSession]
@ioc.entity
def bindersService(): return list(chain((bindExampleValidations,), binders()))

bind.bindToEntities('example.*.impl.**.*Alchemy', binders=binders)
support.createEntitySetup('example.*.impl.**.*')
support.listenToEntities(SERVICES, listeners=addService(bindersService))
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------
