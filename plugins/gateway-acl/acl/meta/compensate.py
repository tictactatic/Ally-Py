'''
Created on Sep 2, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for ACL compensate access.
'''

from ..api.compensate import Compensate
from .access import AccessMapped
from sql_alchemy.support.util_meta import JSONEncodedDict
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import String

# --------------------------------------------------------------------

class WithCompensate(Compensate):
    '''
    Provides the ACL compensate relation.
    '''
    __table_args__ = dict(mysql_engine='InnoDB')
    
    Access = declared_attr(lambda cls:
             Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'), nullable=False, primary_key=True))
    Path = declared_attr(lambda cls: Column('path', String(255), nullable=False))
    Mapping = declared_attr(lambda cls: Column('mapping', JSONEncodedDict(255), nullable=False))
    # Non REST model attribute --------------------------------------
    access = declared_attr(lambda cls: relationship(AccessMapped, lazy='joined', uselist=False, viewonly=True))
    @declared_attr
    def aclAccessId(cls): raise Exception('An acl access id definition is required')  # @NoSelf
