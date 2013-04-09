'''
Created on Mar 15, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides manipulator structure classes.
'''

from ally.design.processor.spec import IResolver
from collections import Iterable

# --------------------------------------------------------------------

def restructureData(data, mapping, reversed=False):
    '''
    Restructures the data based on the provided mapping.
    
    @param data: dictionary{string: object}
        The data to restructure.
    @param mapping: tuple(string|tuple(string, string))
        The mapping to make the restructure by.
    @param reversed: boolean
        Flag indicating that the mapping should be done in reversed.
    @return: dictionary{string: object}
        The restructured data.
    '''
    assert isinstance(data, dict), 'Invalid data %s' % data
    assert isinstance(mapping, tuple), 'Invalid mapping %s' % mapping
    assert isinstance(reversed, bool), 'Invalid reversed flag %s' % reversed
    
    restructured = {}
    for name in mapping:
        if isinstance(name, tuple):
            if reversed: nameFrom, nameTo = name
            else: nameTo, nameFrom = name
            assert isinstance(nameFrom, str), 'Invalid name from %s' % nameFrom
            assert isinstance(nameTo, str), 'Invalid name to %s' % nameTo
        else:
            assert isinstance(name, str), 'Invalid mapping name %s' % name
            nameFrom = nameTo = name
            
        if nameFrom in data: restructured[nameTo] = data[nameFrom]
    return restructured
    
def restructureResolvers(resolvers, mapping, reversed=False):
    '''
    Restructures the data based on the provided mapping.
    
    @param resolvers: dictionary{string: IResolver}
        The resolvers to restructure.
    @param mapping: Iterable(string|tuple(string, string))
        The mapping to make the restructure by.
    @param reversed: boolean
        Flag indicating that the mapping should be done in reversed.
    @return: dictionary{string: IResolver}
        The restructured resolvers.
    '''
    assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
    assert isinstance(mapping, Iterable), 'Invalid mapping %s' % mapping
    assert isinstance(reversed, bool), 'Invalid reversed flag %s' % reversed
    
    restructured = {}
    for name in mapping:
        if isinstance(name, tuple):
            if reversed: nameFrom, nameTo = name
            else: nameTo, nameFrom = name
            assert isinstance(nameFrom, str), 'Invalid name from %s' % nameFrom
            assert isinstance(nameTo, str), 'Invalid name to %s' % nameTo
        else:
            assert isinstance(name, str), 'Invalid mapping name %s' % name
            nameFrom = nameTo = name
        
        resolver = resolvers.get(nameFrom)
        if resolver:
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
            rresolver = restructured.get(nameTo)
            if rresolver:
                assert isinstance(rresolver, IResolver), 'Invalid resolver %s' % rresolver
                others = set(resolver.list())
                others.difference_update(rresolver.list())
                restructured[nameTo] = rresolver.merge(resolver.copy(others))
            else: restructured[nameTo] = resolver
    return restructured
    
