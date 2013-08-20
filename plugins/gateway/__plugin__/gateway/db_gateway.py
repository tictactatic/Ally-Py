'''
Created on Jan 17, 2012

@package: gateway
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the database settings for the gateway database.
'''

from ally.container import ioc, support
from ally.support.sqlalchemy.session import bindSession
from gateway.meta.metadata_gateway import meta
from sql_alchemy import database_config
from sql_alchemy.database_config import alchemySessionCreator, metas

# --------------------------------------------------------------------

support.include(database_config)

# --------------------------------------------------------------------

alchemySessionCreator = alchemySessionCreator

@ioc.replace(database_url)
def database_url():
    '''This database URL is used for the gateway tables'''
    return 'sqlite:///workspace/shared/gateway.db'

@ioc.before(metas)
def updateMetasForGateway(): metas().append(meta)

# --------------------------------------------------------------------

def bindGatewaySession(proxy): bindSession(proxy, alchemySessionCreator())
