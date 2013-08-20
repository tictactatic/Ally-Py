'''
Created on Aug 19, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Specifications and general functions for ACL.
'''

from ally.api.operator.type import TypeProperty, TypeModel

# --------------------------------------------------------------------

def uniqueNameFor(prop):
    '''
    Provides the unique name for the property type.
    
    @param prop: TypeProperty
        The property type to provide the unique name for.
    @return: string
        The unique name.
    '''
    assert isinstance(prop, TypeProperty), 'Invalid property type %s' % prop
    assert isinstance(prop.parent, TypeModel), 'Invalid property parent %s' % prop.parent
    
    return '%s.%s.%s' % (prop.parent.clazz.__module__, prop.parent.clazz.__name__, prop.name)

