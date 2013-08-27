'''
Created on Aug 26, 2013

@package: gateway acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation that provides the support for ACL internals.
'''

from acl.meta.acl_intern import Path, Method, Type
from ally.api.error import InputError
from ally.support.sqlalchemy.session import openSession
from sqlalchemy.orm.exc import NoResultFound
import re

# --------------------------------------------------------------------

def pathId(path):
    '''
    Provides the path id for the provided path.
    '''
    assert isinstance(path, str), 'Invalid path %s' % path
    session = openSession()
    
    path = path.strip().strip('/')
    items = path.split('/')
    try: pathId, = session.query(Path.id).filter(Path.path == path).one()
    except NoResultFound:
        aclPath = Path()
        aclPath.path = path
        
        for k, item in enumerate(items, 1):
            if item == '*':
                if aclPath.priority is None: aclPath.priority = k
            elif not re.match('\w*$', item):
                raise InputError(_('Invalid path item \'%(item)s\', expected only alpha numeric characters or *'), item=item)
        if aclPath.priority is None: aclPath.priority = 0
        
        session.add(aclPath)
        session.flush((aclPath,))
        pathId = aclPath.id
    
    return items, pathId

def methodId(name):
    '''
    Provides the method id for the provided name.
    '''
    assert isinstance(name, str), 'Invalid name %s' % name
    session = openSession()
    
    name = name.strip().upper()
    try: methodId, = session.query(Method.id).filter(Method.name == name).one()
    except NoResultFound:
        method = Method()
        method.name = name
        session.add(method)
        session.flush((method,))
        methodId = method.id
    return methodId

def typeId(name):
    '''
    Provides the type id for the provided type name.
    '''
    assert isinstance(name, str), 'Invalid type name %s' % name
    session = openSession()
    
    name = name.strip()
    try: typeId, = session.query(Type.id).filter(Type.name == name).one()
    except NoResultFound:
        aclType = Type()
        aclType.name = name
        session.add(aclType)
        session.flush((aclType,))
        typeId = aclType.id
    return typeId
