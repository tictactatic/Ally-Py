'''
Created on Aug 29, 2013

@package: gui core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Gociu

Provides the synchronization with the database for actions.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.execution import Chain
from ally.design.processor.handler import HandlerProcessor, Handler
from ally.support.api.util_service import copyContainer
from ally.support.util_context import asData, attributesOf
from gui.action.api.action import Action, IActionManagerService
import logging
from ally.support.util import modifyFirst

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Solicit(Context):
    '''
    The solicit context.
    '''
    # ---------------------------------------------------------------- Required
    repository = requires(Context)

class Repository(Context):
    '''
    The repository context.
    '''
    # ---------------------------------------------------------------- Required
    actions = requires(list)

class WithTracking(Context):
    '''
    Container for the tracking information.
    '''
    lineNumber = requires(int)
    colNumber = requires(int)

class ActionData(Context):
    '''
    The action container context.
    '''
    # ---------------------------------------------------------------- Required
    path = requires(str)
    label = requires(str)
    script = requires(str)
    navBar = requires(str)
    
class ActionDefinition(ActionData, WithTracking):
    '''
    The action container context.
    '''
    
# --------------------------------------------------------------------

@injected
@setup(Handler, name='synchronizeAction')
class SynchronizeActionHandler(HandlerProcessor):
    '''
    Implementation for a processor that parses XML files based on digester rules.
    '''
    
    actionManagerService = IActionManagerService; wire.entity('actionManagerService')
    
    def __init__(self):
        assert isinstance(self.actionManagerService, IActionManagerService), \
        'Invalid action service %s' % self.actionManagerService
        super().__init__(Repository=Repository)
        
        # will keep a track of the warnings displayed to avoid displaying the same warning multiple times
        self._warnings = set()
        
    def process(self, chain, solicit:Solicit, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Synchronize the actions in the configuration file with the actions in the database.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(solicit, Solicit), 'Invalid solicit %s' % solicit
        if solicit.repository is None or solicit.repository.actions is None: return
        assert isinstance(solicit.repository, Repository), 'Invalid repository %s' % solicit.repository
        
        actionsFromConfig = {}
        # check for actions with the same path -> display warning message
        isWarning = False
        for action in solicit.repository.actions:
            if action.path in actionsFromConfig:
                action1, action2 = action, actionsFromConfig[action.path]
                diffs = self.compareActions(action1, action2)
                if diffs:
                    isWarning = True
                    warningId = '%s_%s_%s' % (action.path, action1.lineNumber, action2.lineNumber)
                    if warningId in self._warnings: continue
                    
                    log.warning('Attributes: "%s" are different for Action with path="%s" at Line %s and Line %s',
                                ', '.join(diffs), action1.path, action1.lineNumber, action2.lineNumber)
                    self._warnings.add(warningId)
                    
            else: actionsFromConfig[action.path] = action
        # if everything was ok, erase all warnings
        if not isWarning and len(self._warnings) > 0: 
            log.warning('Actions OK')
            self._warnings.clear()
            
        actionsFromDb = set(self.actionManagerService.getAll())
        
        for action in sorted(actionsFromConfig.values(), key=lambda action:action.path):
            assert isinstance(action, ActionDefinition), 'Invalid action %s' % action
            data = asData(action, ActionDefinition)
            data = {modifyFirst(name, True): value for name, value in data.items()}
            apiAction = copyContainer(data, Action())
            resolved = False
            if action.path not in actionsFromDb:
                try:
                    self.actionManagerService.insert(apiAction)
                    resolved = True
                except: log.warn('Cannot add action %s, maybe already exists' % apiAction.Path)
                
            if not resolved:
                self.actionManagerService.update(apiAction)
                # except: log.warn('Cannot update action %s' % apiAction.Path)
                actionsFromDb.discard(action.path)
        
        for path in actionsFromDb: self.actionManagerService.delete(path)

    def compareActions(self, action1, action2):
        '''
        Compares two actions by their attributes and returns a list of attributes that have different values 
        or an empty list.
        '''
        assert isinstance(action1, ActionDefinition), 'Invalid action %s' % action1
        assert isinstance(action2, ActionDefinition), 'Invalid action %s' % action2
        
        differences = []
        data1, data2 = asData(action1, ActionData), asData(action2, ActionData)
        for name in attributesOf(ActionData):
            if data1.get(name) != data2.get(name): differences.append(name)
        
        return differences
    
