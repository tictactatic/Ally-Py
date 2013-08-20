'''
Created on Jan 28, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL access.
'''

from . import acl_intern
from ..api.access import Access
from .metadata_acl import Base
from ally.support.sqlalchemy.mapper import validate
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint

# --------------------------------------------------------------------

class AccessToType(Base):
    '''
    Provides the Access to Type mapping.
    '''
    __tablename__ = 'acl_access_type'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    accessId = Column('fk_access_id', ForeignKey('acl_access.id', ondelete='CASCADE'), primary_key=True)
    typeId = Column('fk_type_id', ForeignKey(acl_intern.Type.id, ondelete='RESTRICT'), primary_key=True)
    position = Column('position', INTEGER(unsigned=True), autoincrement=False, primary_key=True)
    # Relationships -------------------------------------------------
    type = relationship(acl_intern.Type, lazy='joined', cascade='all')

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
    Types = association_proxy('types', 'type.name')
    ShadowOf = Column('fk_shadow_of_id', ForeignKey('acl_access.id', ondelete='CASCADE'))
    # Non REST model attribute --------------------------------------
    pathId = Column('fk_path_id', ForeignKey(acl_intern.Path.id, ondelete='RESTRICT'), nullable=False)
    methodId = Column('fk_method_id', ForeignKey(acl_intern.Method.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    path = relationship(acl_intern.Path, lazy='joined', uselist=False)
    method = relationship(acl_intern.Method, lazy='joined', uselist=False)
    types = relationship(AccessToType, order_by=AccessToType.position, lazy='joined', cascade='all')
