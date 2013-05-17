'''
Created on Mar 4, 2012

@package: administration introspection
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the components introspection.
'''

from ..api.component import IComponentService, Component
from ally.container.aop import modulesIn
from ally.container.ioc import injected
from ally.container.support import setup
from ally.exception import InputError, Ref
from ally.internationalization import _
from ally.support.api.util_service import processCollection
from os import path
import sys

# --------------------------------------------------------------------

@injected
@setup(IComponentService, name='componentService')
class ComponentService(IComponentService):
    '''
    Provides the implementation for @see: IComponentService.
    '''

    package = '__setup__'
    # The top package where the components are configured
    default_locale = 'en'
    # The default locale in which the components are defined.

    def __init__(self):
        '''
        Constructs the components service.
        '''
        assert isinstance(self.package, str), 'Invalid package pattern %s' % self.package
        assert isinstance(self.default_locale, str), 'Invalid locale %s' % self.default_locale

    def getById(self, id):
        '''
        @see: IComponentService.getById
        '''
        assert isinstance(id, str), 'Invalid id %s' % id
        modules = modulesIn('%s.%s' % (self.package, id)).asList()
        if len(modules) != 1: raise InputError(Ref(_('Invalid component id'), ref=Component.Id))
        
        c = Component()
        c.Id = id
        m = sys.modules.get(modules[0])
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
            
        return c

    def getComponents(self, q=None, **options):
        '''
        @see: IComponentService.getComponents
        '''
        modules = modulesIn('%s.*' % self.package).asList()
        modules.sort()
        modules = (module[len(self.package) + 1:] for module in modules)
        return processCollection(modules, Component, q, self.getById, withTotal=True, **options)
