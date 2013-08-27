'''
Created on Jan 28, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL access.
'''

from ..api.access import Access, Entry, Property
from .metadata_acl import Base
from .acl_intern import Path, Method, Type
from ally.support.sqlalchemy.mapper import validate
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import String

# --------------------------------------------------------------------

@validate
class AccessMapped(Base, Access):
    '''
    Provides the ACL access mapping.
    '''
    __tablename__ = 'acl_access'
    __table_args__ = (UniqueConstraint('fk_path_id', 'fk_method_id', name='uix_acl_access'), dict(mysql_engine='InnoDB'))
    
    Id = Column('id', INTEGER(unsigned=True), autoincrement=False, primary_key=True)
    Priority = association_proxy('path', 'priority')
    Shadowing = Column('fk_shadowing_id', ForeignKey('acl_access.id', ondelete='CASCADE'))
    Shadowed = Column('fk_shadowed_id', ForeignKey('acl_access.id', ondelete='CASCADE'))
    Hash = Column('hash', String(50), nullable=False, unique=True)
    # Non REST model attribute --------------------------------------
    pathId = Column('fk_path_id', ForeignKey(Path.id, ondelete='RESTRICT'), nullable=False)
    methodId = Column('fk_method_id', ForeignKey(Method.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    path = relationship(Path, lazy='joined', uselist=False)
    method = relationship(Method, lazy='joined', uselist=False)
    # REST model attribute with name conflicts ----------------------
    Path = association_proxy('path', 'path')
    Method = association_proxy('method', 'name')
    
@validate
class EntryMapped(Base, Entry):
    '''
    Provides the ACL access entry mapping.
    '''
    __tablename__ = 'acl_access_entry'
    __table_args__ = (UniqueConstraint('fk_access_id', 'position', name='uix_acl_access_entry'), dict(mysql_engine='InnoDB'))
    
    Position = Column('position', INTEGER(unsigned=True))
    Shadowing = Column('shadowing_position', INTEGER(unsigned=True))
    Shadowed = Column('shadowed_position', INTEGER(unsigned=True))
    # Non REST model attribute --------------------------------------
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    accessId = Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'), nullable=False)
    typeId = Column('fk_type_id', ForeignKey(Type.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    type = relationship(Type, lazy='joined', uselist=False)
    # REST model attribute with name conflicts ----------------------
    Type = association_proxy('type', 'name')
    
@validate
class PropertyMapped(Base, Property):
    '''
    Provides the ACL access property mapping.
    '''
    __tablename__ = 'acl_access_property'
    __table_args__ = (UniqueConstraint('fk_access_id', 'name', name='uix_acl_access_property'), dict(mysql_engine='InnoDB'))
    
    Name = Column('name', String(255))
    # Non REST model attribute --------------------------------------
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    accessId = Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'), nullable=False)
    typeId = Column('fk_type_id', ForeignKey(Type.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    type = relationship(Type, lazy='joined', uselist=False)
    # REST model attribute with name conflicts ----------------------
    ype = association_proxy('type', 'name')
    
