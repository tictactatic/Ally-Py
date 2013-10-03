'''
Created on Mar 4, 2012

@package: administration introspection
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the components introspection.
'''

from admin.api.domain_admin import modelAdmin
from ally.api.config import service, query
from ally.api.criteria import AsLike, AsBoolean
from ally.api.option import Slice #@UnusedImport
from ally.support.api.entity import IEntityGetPrototype, IEntityQueryPrototype

# --------------------------------------------------------------------

@modelAdmin(id='Id')
class Component:
    '''
    Provides the component data.
    '''
    Id = str
    Name = str
    Group = str
    Version = str
    Description = str
    Loaded = bool
    Path = str
    InEgg = bool

# --------------------------------------------------------------------

@query(Component)
class QComponent:
    '''
    Provides the component query.
    '''
    name = AsLike
    group = AsLike
    version = AsLike
    loaded = AsBoolean
    path = AsLike
    inEgg = AsBoolean

# --------------------------------------------------------------------

@service(('Entity', Component), ('QEntity', QComponent))
class IComponentService(IEntityGetPrototype, IEntityQueryPrototype):
    '''
    Provides services for ally components.
    '''
