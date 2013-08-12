'''
Created on Aug 12, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Specifications for tree item change notifier.
'''

from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.support.util_spec import IDo

# --------------------------------------------------------------------

CREATED = 'created'  # The create flag.
MODIFIED = 'modified'  # The create flag.
DELETED = 'deleted'  # The create flag.

# --------------------------------------------------------------------

class Register(Context):
    '''
    The notifier register context.
    '''
    # ---------------------------------------------------------------- Required
    items = requires(dict)
    
# --------------------------------------------------------------------

class Notification(Context):
    '''
    The notification context.
    '''
    # ---------------------------------------------------------------- Defined
    changes = defines(list, doc='''
    @rtype: list[Context]
    The contexts changes.
    ''')

class Change(Context):
    '''
    The change context.
    '''
    # ---------------------------------------------------------------- Defined
    item = defines(Context, doc='''
    @rtype: Context
    The item that changed.
    ''')
    change = defines(str, doc='''
    @rtype: string
    Indicates the change status.
    ''')
    
class Item(Context):
    '''
    The item context.
    '''
    # ---------------------------------------------------------------- Defined
    parent = defines(Context, doc='''
    @rtype: Context
    The parent item.
    ''')
    name = defines(str, doc='''
    @rtype: string
    The item name.
    ''')
    hash = defines(str, doc='''
    @rtype: datetime
    The item status hash.
    ''')
    children = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The children items.
    ''')
    doGetStream = defines(IDo, doc='''
    @rtype: callable() -> IInputStream
    Provides the input stream for item.
    ''')
