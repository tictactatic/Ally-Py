'''
Created on Mar 4, 2012

@package: administration introspection
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the components introspection.
'''

from ..api.component import IComponentService, Component
from ally.api.error import IdError
from ally.container.aop import modulesIn
from ally.container.ioc import injected
from ally.container.support import setup
from ally.support.api.util_service import processCollection
from collections import OrderedDict
from os import path
import sys

# --------------------------------------------------------------------

class ComponentServiceBase:
    '''
    Provides the base implementation for component services.
    '''
    
    package = str
    # The top package where the components are configured.
    Component = Component
    # The model class to use as a component.

    def __init__(self):
        '''
        Constructs the components service.
        '''
        assert isinstance(self.package, str), 'Invalid package %s' % self.package
        assert issubclass(self.Component, Component), 'Invalid component class %s' % Component
        
        self._modules = None
        
    def getById(self, id):
        '''
        Provides the component based on the provided id.
        @see: IComponentService.getById
        '''
        assert isinstance(id, str), 'Invalid id %s' % id
        module = self.modules().get(id)
        if module is None: raise IdError(self.Component)
        
        c = self.Component()
        assert isinstance(c, Component), 'Invalid component %s' % c
        
        c.Id = id
        m = sys.modules.get(module)
        if m:
            c.Loaded = True
            c.Name = getattr(m, 'NAME', None)
            c.Group = getattr(m, 'GROUP', None)
            c.Version = getattr(m, 'VERSION', None)
            c.Description = getattr(m, 'DESCRIPTION', None)
            c.Path = path.relpath(path.dirname(path.dirname(path.dirname(m.__file__))))
            c.InEgg = not path.isfile(m.__file__)
        else:
            c.Loaded = False
            
        return c

    def getAll(self, q=None, **options):
        '''
        Provides the components ids.
        @see: IComponentService.getAll
        '''
        return processCollection(self.modules().keys(), self.Component, q, self.getById, **options)
    
    # ----------------------------------------------------------------
    
    def modules(self):
        '''
        Provides the modules in the current distribution.
        '''
        if self._modules is None:
            modules = modulesIn('%s.*' % self.package).asList()
            modules.sort()
            self._modules = OrderedDict(((module[len(self.package) + 1:], module) for module in modules))
        return self._modules

# --------------------------------------------------------------------

@injected
@setup(IComponentService, name='componentService')
class ComponentService(ComponentServiceBase, IComponentService):
    '''
    Provides the implementation for @see: IComponentService.
    '''

    package = '__setup__'
    # The top package where the components are configured

