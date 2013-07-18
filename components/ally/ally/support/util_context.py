'''
Created on Jul 18, 2013

@package: ally base
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides utility functions for processor contexts.
'''

from ally.design.processor.context import Context, Object, attributeOf
from ally.design.processor.spec import ContextMetaClass, IAttribute
from collections import Iterable

# --------------------------------------------------------------------

def namesOf(clazz):
    '''
    Provides the context attributes names.
    
    @param clazz: ContextMetaClass
        The context class to provide the attributes names for.
    @return: set(string)
        The attribute names.
    '''
    assert isinstance(clazz, ContextMetaClass)
    return set(clazz.__attributes__)

def asData(context, *classes):
    '''
    Provides the data that is represented in the provided context classes.
    
    @param context: object
        The context object to get the data from.
    @param classes: arguments[ContextMetaClass]
        The context classes to construct the data based on.
    '''
    assert isinstance(context, Context), 'Invalid context %s' % context

    common = set(context.__attributes__)
    for clazz in classes:
        assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
        common.intersection_update(clazz.__attributes__)
        
    data = {}
    for name in common:
        if context.__attributes__[name] in context: data[name] = getattr(context, name)

    return data

# --------------------------------------------------------------------

def pushIn(dest, *srcs, interceptor=None, exclude=None):
    '''
    Pushes in the destination context data from the source context(s).
    
    @param dest: object
        The destination context object to get the data from.
    @param srcs: arguments[Context|dictionary{string: object}]
        Sources to copy data from, attention the order is important since if the first context has no value
        for an attribute then the second one is checked and so on.
    @param interceptor: callable(object) -> object|None
        An interceptor callable to be called before setting the value on the destination.
    @param exclude: string|ContextMetaClass|Iterable(string|ContextMetaClass)|None
        The attribute(s) of ContextMetaClass to be excluded from the push.
    @return: object
        The destination context after copy.
    '''
    assert isinstance(dest, Object), 'Invalid destination context %s' % dest
    assert srcs, 'At least one source is required'
    assert interceptor is None or callable(interceptor), 'Invalid interceptor %s' % interceptor
    
    if exclude is not None:
        excludes = set()
        if isinstance(exclude, ContextMetaClass): excludes.update(exclude.__attributes__) 
        elif isinstance(exclude, str): excludes.add(exclude)
        else:
            assert isinstance(exclude, Iterable), 'Invalid exclude %s' % exclude
            for name in exclude:
                if isinstance(name, ContextMetaClass): excludes.update(name.__attributes__)
                else:
                    assert isinstance(name, str), 'Invalid exclude name %s' % name
                    excludes.add(name)
    else: excludes = frozenset()
    
    for name in dest.__attributes__:
        if name in excludes: continue
        found = False
        for src in srcs:
            if isinstance(src, Context):
                attribute = src.__attributes__.get(name)
                if attribute and attribute in src: found, value = True, getattr(src, name)
            else:
                assert isinstance(src, dict), 'Invalid source %s' % src
                if name in src: found, value = True, src[name]
            
            if found:
                if interceptor is not None: value = interceptor(value)
                setattr(dest, name, value)
                break
    
    return dest

def cloneCollection(value):
    '''
    Interceptor to be used on the 'pushIn' function that creates new collections with the same items.
    The collections copied are: set, dict, list.
    
    @param value: object
        The value to intercept.
    @return: object
        The clone collection if is the case or the same value.
    '''
    if value is None: return
    clazz = value.__class__
    if clazz == set: return set(value)
    elif clazz == dict: return dict(value)
    elif clazz == list: return list(value)
    return value

# --------------------------------------------------------------------

def findFirst(context, search, attribute, maximum=1000):
    '''
    Finds the first value that is not None for the provided attribute, the search will be made based on the search 
    attribute which must be for a context.
    
    @param context: Context
        The context to search in.
    @param search: Context.attribute(Context)
        The context attribute to search based on.
    @param attribute: Context.attribute
        The context attribute to provide the first value for.
    @param maximum: integer
        The maximum search depth to be made, after this None will be returned.
    @return: object|None
        The found value or None if no value could be found.
    '''
    assert isinstance(context, Context), 'Invalid context %s' % context
    sattr = attributeOf(search)
    assert isinstance(sattr, IAttribute), 'Invalid search attribute %s' % search
    attr = attributeOf(attribute)
    assert isinstance(attr, IAttribute), 'Invalid attribute %s' % attr
    assert isinstance(maximum, int), 'Invalid maximum %s' % maximum
    
    while context is not None:
        assert isinstance(context, Context), 'Invalid context %s' % context
        if maximum <= 0: return
        value = getattr(context, attr.__name__)
        if value is not None: return value
        if sattr in context: context = getattr(context, sattr.__name__)
        else: context = None
        maximum -= 1
