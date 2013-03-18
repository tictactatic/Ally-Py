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
from ally.api.extension import IterPart
from ally.container import wire
from ally.container.aop import modulesIn
from ally.container.ioc import injected
from ally.container.support import setup
from ally.exception import InputError, Ref
from ally.internationalization import _
from ally.support.api.util_service import trimIter
from os import path
import sys

# --------------------------------------------------------------------

@injected
@setup(IPluginService, name='pluginService')
class PluginService(IPluginService):
    '''
    Provides the implementation for @see: IPluginService.
    '''

    default_locale = 'en'; wire.config('default_locale', doc='''
    The default locale in which the plugins are defined
    ''')

    componentService = IComponentService; wire.entity('componentService')

    def __init__(self):
        '''
        Constructs the plugins service.
        '''
        assert isinstance(self.default_locale, str), 'Invalid locale %s' % self.default_locale
        assert isinstance(self.componentService, IComponentService), 'Invalid component service %s' % self.componentService

    def getById(self, id):
        '''
        @see: IPluginService.getById
        '''
        assert isinstance(id, str), 'Invalid id %s' % id
        modules = modulesIn('%s.%s' % ('__plugin__', id)).asList()
        if len(modules) != 1: raise InputError(Ref(_('Invalid plugin id'), ref=Plugin.Id))
        return self.pluginFor(modules[0])

    def getPlugins(self, offset=None, limit=None):
        '''
        @see: IPluginService.getPlugins
        '''
        modules = modulesIn('__plugin__.*').asList()
        modules.sort()

        return IterPart(trimIter((self.idOf(module) for module in modules), len(modules), offset, limit),
                        len(modules), offset, limit)

    # ----------------------------------------------------------------
    
    def idOf(self, module):
        '''
        Provides the id base don module.
        '''
        assert isinstance(module, str), 'Invalid module %s' % module
        return module[len('__plugin__') + 1:]

    def pluginFor(self, module):
        '''
        Create a plugin based on the provided module.
        
        @param module: string
            The module to create a plugin for.
        @param components: dictionary{string, string}|None
            A dictionary having as a key the component path and as a value the component id.
        @return: Plugin
            The plugin reflecting the module.
        '''
        assert isinstance(module, str), 'Invalid module %s' % module

        c = Plugin()
        c.Id = self.idOf(module)

        m = sys.modules.get(module)
        if m:
            c.Loaded = True
            c.Name = getattr(m, 'NAME', None)
            c.Group = getattr(m, 'GROUP', None)
            c.Version = getattr(m, 'VERSION', None)
            c.Locale = getattr(m, 'LANGUAGE', self.default_locale)
            c.Description = getattr(m, 'DESCRIPTION', None)
            c.Path = path.relpath(path.dirname(path.dirname(path.dirname(m.__file__))))
            c.InEgg = not path.isfile(m.__file__)
        else:
            c.Loaded = False
        try: c.Component = next(iter(self.componentService.getComponents(limit=1, q=QComponent(path=c.Path)))).Id
        except StopIteration: pass

        return c
