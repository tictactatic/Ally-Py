'''
Created on Mar 4, 2012

@package: administration introspection
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the plugin introspection.
'''

from ..api.component import Component, QComponent, IComponentService
from admin.api.domain_admin import modelAdmin
from ally.api.config import service, query

# --------------------------------------------------------------------

@modelAdmin
class Plugin(Component):
    '''
    Provides the plugin data.
    '''
    Component = Component
    
# --------------------------------------------------------------------

@query(Plugin)
class QPlugin(QComponent):
    '''
    Provides the component query.
    '''
    
# --------------------------------------------------------------------

@service((Component, Plugin), (QComponent, QPlugin))
class IPluginService(IComponentService):
    '''
    Provides services for ally plugins.
    '''
