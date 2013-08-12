'''
Created on Aug 12, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the notifying for a specific root path.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing
from ally.design.processor.handler import HandlerBranching

# --------------------------------------------------------------------

class Register(Context):
    '''
    The notifier register context.
    '''
    # ---------------------------------------------------------------- Defined
    items = defines(dict, doc='''
    @rtype: dictionary{string: Context}
    The items registered for root.
    ''')
    item = defines(Context, doc='''
    @rtype: Context
    The item parent to register to.
    ''')
    
class Notification(Context):
    '''
    The notification context.
    '''
    # ---------------------------------------------------------------- Required
    changes = requires(list)

class Change(Context):
    '''
    The change context.
    '''
    # ---------------------------------------------------------------- Required
    item = requires(Context)

class ItemRoot(Context):
    '''
    The item context.
    '''
    # ---------------------------------------------------------------- Required
    parent = requires(Context)
    path = requires(list)
    
# --------------------------------------------------------------------

@injected
class PathRouterHandler(HandlerBranching):
    '''
    Implementation for a processor that notifying for a root path.
    '''
    
    root = list
    # The root names to provide notifications for.
    # The root can contain place holders like '*' for a single path item or '**' for multiple path items.
    assembly = Assembly
    # The assembly to be used for processing file system notifications for root path.
    
    def __init__(self):
        assert isinstance(self.root, list), 'Invalid root names %s' % self.root
        assert self.root, 'At least one name is required'
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        super().__init__(Branch(self.assembly).include('register', ('change', 'Change')))
        
    def process(self, chain, processing, Item:ItemRoot, register:Register=None, notification:Notification=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process root paths notifications.
        '''
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert issubclass(Item, ItemRoot), 'Invalid item class %s' % Item
        if register:
            assert isinstance(register, Register), 'Invalid register %s' % register
            for name in self.root: register.item = Item(name=name, item=register.item)
            processing.wingIn(chain, True)
        
        if notification:
            assert isinstance(notification, Notification), 'Invalid notification %s' % notification
            #TODO: implement the * and ** place holders or make the root path a pattern like string.
            if notification.changes:
                for change in notification.changes:
                    assert isinstance(change, Change), 'Invalid change %s' % change
                    assert isinstance(change.item, ItemRoot), 'Invalid item %s' % change.item
                    
                    if len(self.root) > len(change.item.path): continue
                    
                    if self.root == change.item.path[:len(self.root)]:
                        processing.wingIn(chain, change=change)
