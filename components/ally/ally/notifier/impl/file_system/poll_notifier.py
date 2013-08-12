'''
Created on Aug 12, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the file system polling and notifying.
'''

from ally.container.ioc import injected
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import attribute
from ally.design.processor.execution import Processing, FILL_CLASSES
from ally.notifier.spec import Register, Notification, Item, MODIFIED, DELETED
from collections import deque
from os import listdir, stat
from os.path import join, isdir, exists

# --------------------------------------------------------------------

class FSItem(Item):
    '''
    The file system item context.
    '''
    # ---------------------------------------------------------------- Defined
    lastModified = attribute(int, doc='''
    @rtype: integer
    The time of the modification.
    ''')
    
# --------------------------------------------------------------------

@injected
class PollNotifier:
    '''
    Implementation that provides the file system polling and notifying.
    '''
    
    rootsFolders = dict
    # Contains as a key the root folder name and as a value the full path
    # where the folder is found.
    assembly = Assembly
    # The assembly to be used for processing file system notifications.
    
    def __init__(self):
        assert isinstance(self.rootsFolders, dict), 'Invalid roots folders %s' % self.rootsFolders
        assert isinstance(self.assembly, Assembly), 'Invalid assembly %s' % self.assembly
        if __debug__:
            for name, path in self.rootsFolders.items():
                assert isinstance(name, str), 'Invalid name %s' % name
                assert isinstance(path, str), 'Invalid path %s' % path
                
        proc = self.assembly.create(register=Register, notification=Notification, Item=FSItem)
        self._processing = proc
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        arg = proc.execute(FILL_CLASSES, register=proc.ctx.register())
        assert isinstance(arg.register, Register), 'Invalid register %s' % arg.register
        self.items = arg.register.items or {}
        
        for item in self.items:
            assert isinstance(item, FSItem), 'Invalid item %s' % item
            assert item.name in self.rootsFolders, 'There is no mapping for \'%s\'' % item.name
    
        #TODO: add scanining thread.
    
    def scan(self):
        '''
        Scan the file changes.
        '''
        proc = self._processing
        assert isinstance(proc, Processing), 'Invalid processing %s' % proc
        
        stack, changes = deque(), []
        stack.extend((self.rootsFolders[item.name], item) for item in self.items)
        while stack:
            path, item = stack.popleft()
            assert isinstance(item, FSItem), 'Invalid item %s' % item
            
            if item.doGetStream:  # The item is a file.
                if not exists(path):
                    # TODO: check if is not actually a folder.
                    changes.append(proc.ctx.Change(item=item, change=DELETED))
                else:
                    stat = stat(path)
                    lasModified = max(stat.st_ctime, stat.st_mtime)
                    if item.lastModified != lasModified:
                        item.lastModified = lasModified
                        changes.append(proc.ctx.Change(item=item, change=MODIFIED))
            # TODO: check if is folder and and handle it.
            
            if not isdir(path): continue
            stack.extend(join(path, spath) for spath in listdir(path))
            
        if changes:
            proc.execute(notification=proc.ctx.notification(changes=changes))
