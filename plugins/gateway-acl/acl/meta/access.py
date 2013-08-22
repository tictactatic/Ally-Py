'''
Created on Jan 28, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL access.
'''

from . import acl_intern
from ..api.access import Access, Entry, Property
from .metadata_acl import Base
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
    Path = association_proxy('path', 'path')
    Method = association_proxy('method', 'name')
    Priority = association_proxy('path', 'priority')
    Shadowing = Column('fk_shadowing_id', ForeignKey('acl_access.id', ondelete='CASCADE'))
    Shadowed = Column('fk_shadowed_id', ForeignKey('acl_access.id', ondelete='CASCADE'))
    Hash = Column('hash', String(30), nullable=False, unique=True)
    # Non REST model attribute --------------------------------------
    pathId = Column('fk_path_id', ForeignKey(acl_intern.Path.id, ondelete='RESTRICT'), nullable=False)
    methodId = Column('fk_method_id', ForeignKey(acl_intern.Method.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    path = relationship(acl_intern.Path, lazy='joined', uselist=False)
    method = relationship(acl_intern.Method, lazy='joined', uselist=False)
    
@validate
class EntryMapped(Base, Entry):
    '''
    Provides the ACL access entry mapping.
    '''
    __tablename__ = 'acl_access_entry'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    Position = Column('position', INTEGER(unsigned=True), autoincrement=False, primary_key=True)
    Shadowing = Column('shadowing_position', INTEGER(unsigned=True))
    Shadowed = Column('shadowed_position', INTEGER(unsigned=True))
    Type = association_proxy('type', 'name')
    # Non REST model attribute --------------------------------------
    accessId = Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'), nullable=False, primary_key=True)
    typeId = Column('fk_type_id', ForeignKey(acl_intern.Type.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    type = relationship(acl_intern.Type, lazy='joined', uselist=False)
    
@validate
class PropertyMapped(Base, Property):
    '''
    Provides the ACL access property mapping.
    '''
    __tablename__ = 'acl_access_property'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    Name = Column('name', String(255), primary_key=True)
    Type = association_proxy('type', 'name')
    # Non REST model attribute --------------------------------------
    accessId = Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'), nullable=False, primary_key=True)
    typeId = Column('fk_type_id', ForeignKey(acl_intern.Type.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    type = relationship(acl_intern.Type, lazy='joined', uselist=False)
    
