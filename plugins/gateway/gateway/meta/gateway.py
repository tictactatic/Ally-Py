'''
Created on Jan 28, 2013

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for gateway data.
'''

from .metadata_gateway import Base
from sqlalchemy.schema import Column
from sqlalchemy.types import String, BLOB, INTEGER

# --------------------------------------------------------------------

class GatewayData(Base):
    '''
    Provides the gateway data.
    '''
    __tablename__ = 'gateway'

    name = Column('name', String(255), primary_key=True)
    hash = Column('hash', INTEGER, unique=True, nullable=False)
    identifier = Column('identifier', BLOB, nullable=False)
    navigate = Column('navigate', BLOB, nullable=False)

