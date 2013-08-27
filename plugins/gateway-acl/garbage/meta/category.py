'''
Created on Aug 26, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL category.
'''

from .access import AccessMapped, EntryMapped, PropertyMapped
from .filter import FilterMapped
from .metadata_acl import Base
from sqlalchemy.dialects.mysql.base import INTEGER
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
    
# --------------------------------------------------------------------

class Category(Base):
    '''
    Provides the ACL category.
    '''
    __tablename__ = 'acl_category'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    
class CategoryAccess(Base):
    '''
    Provides the Group to Access mapping.
    '''
    __tablename__ = 'acl_category_access'
    __table_args__ = (UniqueConstraint('fk_category_id', 'fk_access_id', name='uix_acl_category_access'),
                      dict(mysql_engine='InnoDB'))
    
    id = Column('id', INTEGER(unsigned=True), primary_key=True)
    categoryId = Column('fk_category_id', ForeignKey(Category.id, ondelete='CASCADE'))
    accessId = Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'))
    
class CAEntryFilter(Base):
    '''
    Provides the Entry to Filter mapping.
    '''
    __tablename__ = 'acl_category_access_entry_filter'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    categoryAccessId = Column('fk_category_access_id', ForeignKey(CategoryAccess.id, ondelete='CASCADE'), primary_key=True)
    entryId = Column('fk_entry_id', ForeignKey(EntryMapped.id, ondelete='CASCADE'), primary_key=True)
    filterId = Column('fk_filter_id', ForeignKey(FilterMapped.id, ondelete='CASCADE'), primary_key=True)
    
class CAPropertyFilter(Base):
    '''
    Provides the Property to Filter mapping.
    '''
    __tablename__ = 'acl_category_access_property_filter'
    __table_args__ = dict(mysql_engine='InnoDB')
    
    categoryAccessId = Column('fk_category_access_id', ForeignKey(CategoryAccess.id, ondelete='CASCADE'), primary_key=True)
    propertyId = Column('fk_property_id', ForeignKey(PropertyMapped.id, ondelete='CASCADE'), primary_key=True)
    filterId = Column('fk_filter_id', ForeignKey(FilterMapped.id, ondelete='CASCADE'), primary_key=True)

