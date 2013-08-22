'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL filter.
'''

from . import acl_intern
from ..api.filter import Filter
from .metadata_acl import Base
from ally.support.sqlalchemy.mapper import validate
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import String

# --------------------------------------------------------------------

class FilterToPath(Base):
    '''
    Provides the Filter to Path mapping.
    '''
    __tablename__ = 'acl_filter_path'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    filterId = Column('fk_filter_id', ForeignKey('acl_filter.id', ondelete='CASCADE'))
    pathId = Column('fk_path_id', ForeignKey(acl_intern.Path.id, ondelete='RESTRICT'), primary_key=True)
    # Relationships -------------------------------------------------
    path = relationship(acl_intern.Path, lazy='joined', cascade='all')

@validate
class FilterMapped(Base, Filter):
    '''
    Provides the ACL filter mapping.
    '''
    __tablename__ = 'acl_filter'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    Name = Column('name', String(255), nullable=False, unique=True)
    Target = association_proxy('target', 'name')
    Paths = association_proxy('paths', 'path.path')
    # Non REST model attribute --------------------------------------
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    targetId = Column('fk_type_id', ForeignKey(acl_intern.Type.id, ondelete='RESTRICT'), nullable=False)
    # Relationships -------------------------------------------------
    target = relationship(acl_intern.Type, lazy='joined', uselist=False)
    paths = relationship(FilterToPath, lazy='joined', cascade='all')
