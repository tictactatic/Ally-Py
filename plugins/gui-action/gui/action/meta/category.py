'''
Created on Sep 4, 2013

@package: gui action
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for gui actions category.
'''

from .action import ActionMapped
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.schema import Column, ForeignKey

# --------------------------------------------------------------------

class WithCategoryAction:
    '''
    Provides the action category relation definition.
    '''
    __table_args__ = dict(mysql_engine='InnoDB')

    actionPath = declared_attr(lambda cls:
                 Column('fk_action_path', ForeignKey(ActionMapped.Path, ondelete='CASCADE'), primary_key=True))
    @declared_attr
    def categoryId(cls): raise Exception('A category id definition is required')  # @NoSelf
