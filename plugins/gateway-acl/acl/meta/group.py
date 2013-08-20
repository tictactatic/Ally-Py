'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL group.
'''

from ..api.group import Group
from .access import AccessMapped
from .filter import FilterMapped
from .metadata_acl import Base
from ally.support.sqlalchemy.mapper import validate
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import String

# --------------------------------------------------------------------

class AccessToGroup(Base):
    '''
    Provides the Access to Group mapping.
    '''
    __tablename__ = 'acl_access_group'
    __table_args__ = (UniqueConstraint('fk_access_id', 'fk_group_id', name='uix_acl_access_group'), dict(mysql_engine='InnoDB'))
    
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    accessId = Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'))
    groupId = Column('fk_group_id', ForeignKey('acl_group.id', ondelete='CASCADE'))
    
class FilterToEntry(Base):
    '''
    Provides the Filter to Entry mapping.
    '''
    __tablename__ = 'acl_filter_access_entry'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    accessGroupId = Column('fk_access_group_id', ForeignKey(AccessToGroup.id, ondelete='CASCADE'), primary_key=True)
    filterId = Column('fk_filter_id', ForeignKey(FilterMapped.id, ondelete='CASCADE'), primary_key=True)
    position = Column('position', INTEGER(unsigned=True), autoincrement=False, primary_key=True)
    
@validate
class GroupMapped(Base, Group):
    '''
    Provides the ACL group mapping.
    '''
    __tablename__ = 'acl_group'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    Name = Column('name', String(255), nullable=False, unique=True)
    Description = Column('description', String(255))
    Target = association_proxy('target', 'name')
    Paths = association_proxy('paths', 'path.path')
    # Non REST model attribute --------------------------------------
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
