'''
Created on Mar 4, 2012

@package: administration introspection
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the components introspection.
'''

from ..api.component import IComponentService, QComponent
from ..api.plugin import IPluginService, Plugin
from .component import ComponentServiceBase
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup

# --------------------------------------------------------------------

@injected
@setup(IPluginService, name='pluginService')
class PluginService(ComponentServiceBase, IPluginService):
    '''
    Provides the implementation for @see: IPluginService.
    '''
    
    package = '__plugin__'
    # The top package where the plugins are configured
    Component = Plugin
    # The model class to use as a component.
    
    componentService = IComponentService; wire.entity('componentService')

    def __init__(self):
        '''
        Constructs the plugins service.
        '''
        assert isinstance(self.componentService, IComponentService), 'Invalid component service %s' % self.componentService
        super().__init__()

    def getById(self, id):
        '''
        @see: IPluginService.getById
        '''
        p = super().getById(id)
        assert isinstance(p, Plugin), 'Invalid plugin %s' % p
        
        try: p.Component = next(iter(self.componentService.getAll(q=QComponent(path=p.Path), limit=1)))
        except StopIteration: pass

        return p
