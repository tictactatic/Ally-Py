'''
Created on Mar 13, 2013

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides utility functions for handling repository data
'''

from ..spec import IRepository, LIST_UNAVAILABLE, LIST_CLASSES
from ally.support.util_sys import locationStack
from collections import Iterable

# --------------------------------------------------------------------

def hasUnavailable(repository):
    '''
    Check if the repository has unavailable attributes.
    
    @param repository: IRepository
        The repository to check.
    @return: boolean
        True if the repository has unavailable attributes, False otherwise.
    '''
    assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
    # If at least one entry is iterated it means there are unavailable attributes
    if repository.listAttributes(LIST_UNAVAILABLE): return True 
    return False

def reportUnavailable(repository):
    '''
    Creates a report of attributes that are not available in the the repository.
    
    @param repository: IRepository
        The repository to create the report for.
    @return: string
        A report of the unavailable attributes, empty string if all are available.
    '''
    assert isinstance(repository, IRepository), 'Invalid repository %s' % repository
    lines = []
    for key, classes in repository.listAttributes(LIST_UNAVAILABLE, LIST_CLASSES).items():
        lines.append('\t%s.%s used in:' % key)
        assert isinstance(classes, Iterable), 'Invalid classes %s' % classes
        for clazz in classes: lines.append('\t%s' % locationStack(clazz).strip())
    return '\n'.join(lines)
