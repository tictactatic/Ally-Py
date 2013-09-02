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
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import String
import json

# --------------------------------------------------------------------

class WithCompensate(Compensate):
    '''
    Provides the ACL compensate relation.
    '''
    __table_args__ = dict(mysql_engine='InnoDB')
    
    Access = declared_attr(lambda cls:
             Column('fk_access_id', ForeignKey(AccessMapped.Id, ondelete='CASCADE'), nullable=False, primary_key=True))
    Path = declared_attr(lambda cls:
           Column('path', String(255), nullable=False))
    @hybrid_property
    def Mapping(self):
        try: return self._mapping
        except AttributeError:
            if self.mapping:
                # We need to recreate the dictionary with int key since the json transforms them to strings.
                self._mapping = {int(key): value for key, value in json.loads(self.mapping).items()}
                return self._mapping
    @Mapping.setter
    def MappingSet(self, value):
        self._mapping = value
        self.mapping = json.dumps(value, sort_keys=True)
        
    # Non REST model attribute --------------------------------------
    mapping = declared_attr(lambda cls: Column('mapping', String(255), nullable=False))
    access = declared_attr(lambda cls: relationship(AccessMapped, lazy='joined', uselist=False, viewonly=True))
    @declared_attr
    def aclAccessId(cls): raise Exception('An acl access id definition is required')  # @NoSelf
