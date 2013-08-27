'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL filter.
'''

from ..api.filter import Filter, Entry
from .acl_intern import Path, Type
from .metadata_acl import Base
from ally.support.sqlalchemy.mapper import validate
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import String

# --------------------------------------------------------------------

@validate
class FilterMapped(Base, Filter):
    '''
    Provides the ACL filter mapping.
    '''
    __tablename__ = 'acl_filter'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    Name = Column('name', String(255), nullable=False, unique=True)
    Target = Column('target_position', INTEGER(unsigned=True), nullable=False)
    Hash = Column('hash', String(50), nullable=False, unique=True)
    # Non REST model attribute --------------------------------------
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    pathId = Column('fk_path_id', ForeignKey(Path.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    path = relationship(Path, lazy='joined', uselist=False)
    # REST model attribute with name conflicts ----------------------
    Path = association_proxy('path', 'path')
    
@validate
class FilterEntryMapped(Base, Entry):
    '''
    Provides the ACL filter entry mapping.
    '''
    __tablename__ = 'acl_filter_entry'
    __table_args__ = (UniqueConstraint('fk_filter_id', 'position', name='uix_acl_filter_entry'), dict(mysql_engine='InnoDB'))
    
    Position = Column('position', INTEGER(unsigned=True), nullable=False)
    # Non REST model attribute --------------------------------------
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    filterId = Column('fk_filter_id', ForeignKey(FilterMapped.id, ondelete='CASCADE'), nullable=False)
    typeId = Column('fk_type_id', ForeignKey(Type.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    type = relationship(Type, lazy='joined', uselist=False)
    # REST model attribute with name conflicts ----------------------
    Type = association_proxy('type', 'name')
