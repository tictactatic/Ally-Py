'''
Created on Aug 18, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL internal mappings.
'''

from .metadata_acl import Base
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.schema import Column
from sqlalchemy.types import String

# --------------------------------------------------------------------

class Path(Base):
    '''
    Provides the ACL path mapping.
    '''
    __tablename__ = 'acl_path'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    path = Column('path', String(255), nullable=False, unique=True)
    priority = Column('priority', INTEGER(unsigned=True))
    # Provides the priority of access objects in creating gateways.
    
class Method(Base):
    '''
    Provides the ACL method mapping.
    '''
    __tablename__ = 'acl_method'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    name = Column('name', String(20), nullable=False, unique=True)

class Type(Base):
    '''
    Provides the ACL type mapping.
    '''
    __tablename__ = 'acl_type'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    name = Column('name', String(255), nullable=False, unique=True)
