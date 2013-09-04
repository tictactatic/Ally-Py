'''
Created on Sep 4, 2013

@package: gui action
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for gui right actions.
'''

from .category import WithCategoryAction
from .metadata_action import Base
from sqlalchemy.schema import Column, ForeignKey
from security.meta.right import RightMapped

# --------------------------------------------------------------------

class RightAction(Base, WithCategoryAction):
    '''
    Provides the Right to Action mapping.
    '''
    __tablename__ = 'gui_action_right'
    
    categoryId = Column('fk_right_id', ForeignKey(RightMapped.Id, ondelete='CASCADE'))
