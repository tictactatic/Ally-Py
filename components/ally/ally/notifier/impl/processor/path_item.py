'''
Created on Aug 12, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the full path for items.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import defines, requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.notifier.spec import CREATED
from collections import deque
from ally.design.processor.execution import Chain

# --------------------------------------------------------------------

class Register(Context):
    '''
    The notifier register context.
    '''
    # ---------------------------------------------------------------- Defined
    items = requires(dict)
    
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
    change = requires(str)

class Item(Context):
    '''
    The item context.
    '''
    # ---------------------------------------------------------------- Defined
    path = defines(list, doc='''
    @rtype: list[string]
    The full path (to root) of the item.
    ''')
    # ---------------------------------------------------------------- Required
    parent = requires(Context)
    name = requires(str)
    children = defines(dict)
    
# --------------------------------------------------------------------

@injected
class PathItemHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the full path for items.
    '''
    
    root = list
    # The root names to provide notifications for.
    assembly = Assembly
    # The assembly to be used for processing file system notifications for root path.
    
    def __init__(self):
        super().__init__(Change=Change, Item=Item)
        
    def process(self, chain, register:Register=None, notification:Notification=None, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Process items path.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        if register: chain.onFinalize(self.processRegister)
        
        if notification:
            assert isinstance(notification, Notification), 'Invalid notification %s' % notification
            
            if notification.changes:
                for change in notification.changes:
                    assert isinstance(change, Change), 'Invalid change %s' % change
                    if change.change != CREATED: continue
                    assert isinstance(change.item, Item), 'Invalid item %s' % change.item
                    item, path = change.item, []
                    while item:
                        if item.path:
                            path.extend(item.path)
                            break
                        path.append(item.name)
                        item = item.parent
                    change.item.path = reversed(path)
                    
    # ----------------------------------------------------------------
    
    def processRegister(self, final, register, **keyargs):
        '''
        Process the registered item paths.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.items: return
        stack = deque()
        stack.extend(([name], item) for name, item in register.items.items())
        while stack:
            path, item = stack.pop()
            assert isinstance(item, Item), 'Invalid item %s' % item
            item.path = path
            if item.children:
                for cname, citem in item.children.items():
                    cpath = list(path)
                    cpath.append(cname)
                    stack.append((cpath, citem))
