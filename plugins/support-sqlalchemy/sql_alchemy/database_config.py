'''
Created on Jan 8, 2012

@package: support sqlalchemy
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains sql alchemy database setup.
'''

from ally.container import ioc, app
from ally.container.error import ConfigError
from ally.design.priority import Priority, PRIORITY_NORMAL
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy import event
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

if __name__ == 'sql_alchemy.database_config': PRIORITY_CREATE_TABLES = PRIORITY_NORMAL
else:
    PRIORITY_CREATE_TABLES = Priority('Create %s tables' % __name__[__name__.rindex('.') + 1:], before=PRIORITY_NORMAL)
    # The create tables priority.

# --------------------------------------------------------------------

@ioc.config
def database_url():
    '''
    The database URL, something like:
        "sqlite:///{database}.db"
        "mysql+mysqlconnector://{user}:{password}@localhost/{database}"
    '''
    raise ConfigError('A database URL is required')

@ioc.config
def alchemy_pool_recycle():
    '''The time to recycle pooled connection'''
    return 3600

@ioc.entity
def alchemySessionCreator(): return sessionmaker(bind=alchemyEngine())

@ioc.entity
def alchemyEngine() -> Engine:
    engine = create_engine(database_url(), pool_recycle=alchemy_pool_recycle())

    if database_url().startswith('sqlite://'):
        @event.listens_for(engine, 'connect')
        def setSQLiteFKs(dbapi_con, con_record):
            dbapi_con.execute('PRAGMA foreign_keys=ON')

    return engine

@ioc.entity
def metas(): return []

# --------------------------------------------------------------------

@app.setup(app.DEVEL, priority=PRIORITY_CREATE_TABLES)
def createTables():
    for meta in metas(): meta.create_all(alchemyEngine())
