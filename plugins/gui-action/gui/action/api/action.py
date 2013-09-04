'''
Created on Feb 27, 2012

@package: gui action
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Balaceanu

Action manager interface and action model 
'''

from ally.api.config import service, call, hints
from ally.api.option import SliceAndTotal  # @UnusedImport
from ally.api.type import Iter, Reference
from ally.support.api.entity import IEntityNQPrototype
from gui.api.domain_gui import modelGui

# --------------------------------------------------------------------

@modelGui(id='Path')
class Action:
    '''
    The object used to create and group actions 
    '''
    Path = str  # path to register in 
    Label = str  # display label
    Script = Reference  # UI script path
    NavBar = str  # href to use for ui controls
    
    def __init__(self, Path=None):
        if Path is not None:
            assert isinstance(Path, str), 'Invalid path %s' % Path
            self.Path = Path

# --------------------------------------------------------------------

@service(('Entity', Action))
class IActionManagerService(IEntityNQPrototype):
    '''
    Provides a container and manager for actions
    '''
    
    @call
    def getActionsRoot(self, **options:SliceAndTotal) -> Iter(Action.Path):
        '''
        Get all root actions registered
        '''
        
    @call(webName='Sub')
    def getSubActions(self, path:Action.Path, **options:SliceAndTotal) -> Iter(Action.Path):
        '''
        Get all actions registered
        '''
hints(IActionManagerService.getAll, webName='All')
