'''
Created on Sep 4, 2013

@package: gui action
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for gui group actions.
'''

from .category import WithCategoryAction
from .metadata_action import Base
from acl.meta.group import GroupMapped
from sqlalchemy.schema import Column, ForeignKey

# --------------------------------------------------------------------

class GroupAction(Base, WithCategoryAction):
    '''
    Provides the Group to Action mapping.
    '''
    __tablename__ = 'gui_action_group'
    
    categoryId = Column('fk_group_id', ForeignKey(GroupMapped.id, ondelete='CASCADE'))
