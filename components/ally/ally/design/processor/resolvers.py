'''
Created on Mar 16, 2013

@package: ally base
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides utility functions for handling resolvers.
'''

from .spec import ContextMetaClass, IAttribute, IResolver, \
    LIST_CLASSES, isNameForClass
from ally.support.util_sys import locationStack
from collections import Iterable

# --------------------------------------------------------------------

def resolverFor(clazz):
    '''
    Provides the resolver for the provided context class.
    
    @param clazz: ContextMetaClass
        The context class to get the resolver for.
    '''
    assert isinstance(clazz, ContextMetaClass), 'Invalid context class %s' % clazz
    theClass = None
    for attribute in clazz.__attributes__.values():
        assert isinstance(attribute, IAttribute), 'Invalid attribute %s' % attribute
        resolverClass = attribute.resolver()
        assert issubclass(resolverClass, IResolver), 'Invalid resolver class %s' % resolverClass
        if theClass is None: theClass = resolverClass
        elif issubclass(theClass, resolverClass): theClass = resolverClass
        else:
            assert issubclass(resolverClass, theClass), \
            'Incompatible resolver classes %s with %s in %s' % (theClass, resolverClass, clazz)
    assert theClass is not None, 'No resolver class could be obtained for %s' % clazz
    return theClass(clazz)

def attributesFor(*resolvers):
    '''
    Provides the common attributes of all resolvers.
    
    @param resolvers: arguments[dictionary{string: IResolver|ContextMetaClass}]
        The resolvers or contexts dictionaries to provide the common attributes for.
    @return: dictionary{string, set(string)}
        The common attributes indexed by context name.
    '''
    assert resolvers, 'At least one resolver is required'
    
    common = {}
    for resolversItem in resolvers:
        assert isinstance(resolversItem, dict), 'Invalid resolvers %s' % resolversItem
        
        for name, resolver in resolversItem.items():
            if isinstance(resolver, ContextMetaClass): resolver = resolverFor(resolver)
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
            
            attributes = common.get(name)
            if attributes is None: attributes = common[name] = set(resolver.list())
            else: attributes.intersection_update(resolver.list())
        
    return {name: attributes for name, attributes in common.items() if attributes}

# --------------------------------------------------------------------

def copyAttributes(resolvers, attributes):
    '''
    Copies from the provided resolvers only the specified attributes.
    
    @param resolvers: dictionary{string: IResolver|ContextMetaClass}
        The resolvers or contexts dictionary to copy from.
    @param attributes: dictionary{string, Iterable(string)}
        The attributes indexed by context name to be copied.
    @return: dictionary{string: IResolver}
        The copied resolvers.
    '''
    assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
    assert isinstance(attributes, dict), 'Invalid attributes %s' % attributes
    
    copy = {}
    for name, resolver in resolvers.items():
        if isinstance(resolver, ContextMetaClass): resolver = resolverFor(resolver)
        assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
        toCopy = attributes.get(name)
        if toCopy:
            assert isinstance(toCopy, Iterable), 'Invalid attributes to copy %s' % toCopy
            copy[name] = resolver.copy(toCopy)
    return copy

def extractContexts(resolvers, contexts):
    '''
    Extracts from the provided resolvers the specified contexts names.
    
    @param resolvers: dictionary{string: IResolver|ContextMetaClass}
        The resolvers or contexts dictionary to extract from.
    @param contexts: Iterable(string)
        The context names to extract.
    @return: dictionary{string: IResolver|ContextMetaClass}
        The extracted resolvers or contexts.
    '''
    assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
    assert isinstance(contexts, Iterable), 'Invalid contexts to extract %s' % contexts
    
    extracted = {}
    for name in contexts:
        assert isinstance(name, str), 'Invalid name %s' % name
        resolver = resolvers.pop(name, None)
        if resolver: extracted[name] = resolver
    return extracted

def resolversFor(contexts):
    '''
    Creates the resolvers dictionary for the provided contexts.
    
    @param other: dictionary{string: ContextMetaClass|IResolver}
        The contexts dictionary to create resolvers for.
    @return: dictionary{string: IResolver}
        The resolvers for the contexts.
    '''
    resolvers = {}
    assert isinstance(contexts, dict), 'Invalid contexts %s' % contexts
    for name, context in contexts.items():
        assert isinstance(name, str), 'Invalid context name %s' % name
        if isinstance(context, IResolver):
            resolvers[name] = context
        else:
            assert isinstance(context, ContextMetaClass), 'Invalid context class %s' % context
            resolvers[name] = resolverFor(context)
    return resolvers

def merge(resolvers, other, joined=True):
    '''
    Merges into the resolvers dictionary the provided resolvers or contexts.
    
    @param resolvers: dictionary{string: IResolver}
        The resolvers to merge in.
    @param other: dictionary{string: IResolver|ContextMetaClass}
        The resolvers or contexts dictionary to merge with.
    @param joined: boolean
        If True then the other resolvers that are not found in resolvers will be pushed into resolvers, for False only the 
        common resolvers are solved.
    @return: dictionary{string: IResolver}
        The same resolvers dictionary after merge.
    '''
    assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
    assert isinstance(other, dict), 'Invalid other resolvers %s' % resolvers
    assert isinstance(joined, bool), 'Invalid joined flag %s' % joined
    
    for name, resolverOther in other.items():
        if isinstance(resolverOther, ContextMetaClass): resolverOther = resolverFor(resolverOther)
        assert isinstance(resolverOther, IResolver), 'Invalid other resolver %s' % resolverOther
        
        resolver = resolvers.get(name)
        if resolver is None:
            if joined: resolvers[name] = resolverOther
        else:
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
            if isNameForClass(name):
                # In case the context name is targeting a class then we better solve the attributes since the order 
                # is not relevant.
                if joined: resolvers[name] = resolver.solve(resolverOther)
                else: resolvers[name] = resolver.solve(resolverOther.copy(resolver.list()))
            else:
                if joined: resolvers[name] = resolver.merge(resolverOther)
                else: resolvers[name] = resolver.merge(resolverOther.copy(resolver.list()))
    return resolvers
            
def solve(resolvers, other, joined=True):
    '''
    Solves into the resolvers dictionary the provided resolvers or contexts.
    
    @param resolvers: dictionary{string: IResolver}
        The resolvers to solve in.
    @param other: dictionary{string: IResolver|ContextMetaClass}
        The resolvers or contexts dictionary to solve with.
    @param joined: boolean
        If True then the other resolvers that are not found in resolvers will be pushed into resolvers, for False only the 
        common resolvers are solved.
    @return: dictionary{string: IResolver}
        The same resolvers dictionary after solve.
    '''
    assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
    assert isinstance(other, dict), 'Invalid other resolvers %s' % other
    assert isinstance(joined, bool), 'Invalid joined flag %s' % joined
    
    for name, resolverOther in other.items():
        if isinstance(resolverOther, ContextMetaClass): resolverOther = resolverFor(resolverOther)
        assert isinstance(resolverOther, IResolver), 'Invalid other resolver %s' % resolverOther
        
        resolver = resolvers.get(name)
        if resolver is None:
            if joined: resolvers[name] = resolverOther
        else:
            assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver 
            if joined: resolvers[name] = resolver.solve(resolverOther)
            else: resolvers[name] = resolver.solve(resolverOther.copy(resolver.list()))
    return resolvers

# --------------------------------------------------------------------

def checkIf(resolvers, *flags):
    '''
    Check if the resolvers have at least one flagged attribute.
    
    @param resolvers: dictionary{string: IResolver}
        The resolvers to check.
    @return: boolean
        True if the resolvers has a flagged attribute, False otherwise.
    '''
    assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers
    assert flags, 'At least one flag is required'
    
    for resolver in resolvers.values():
        assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
        if resolver.list(*flags): return True
    return False

def reportOn(lines, resolvers, *flags):
    '''
    Creates a report of attributes of the resolvers.
    
    @param lines: list[string]
        The report lines where to push the report.
    @param resolvers: dictionary{string: IResolver}
        The resolvers to create the report for.
    @param flags: arguments[object]
        Flags indicating specific attributes to be listed, if no specific flag is provided then all attributes are listed.
    @return: list[string]
        The same report lines list but with the report appended.
    '''
    assert isinstance(lines, list), 'Invalid report lines %s' % lines
    assert isinstance(resolvers, dict), 'Invalid resolvers %s' % resolvers

    for nameCtx, resolver in resolvers.items():
        assert isinstance(resolver, IResolver), 'Invalid resolver %s' % resolver
        for nameAttr, classes in resolver.list(LIST_CLASSES, *flags).items():
            lines.append('\t%s.%s used in:' % (nameCtx, nameAttr))
            assert isinstance(classes, Iterable), 'Invalid classes %s' % classes
            for clazz in classes: lines.append('\t%s' % locationStack(clazz).strip())
    return lines

def reportFor(resolvers, *flags):
    '''
    Creates a report of attributes of the resolvers.
    
    @param resolvers: dictionary{string: IResolver}
        The resolvers to create the report for.
    @param flags: arguments[object]
        Flags indicating specific attributes to be listed, if no specific flag is provided then all attributes are listed.
    @return: string
        A report of the attributes.
    '''
    lines = reportOn([], resolvers, *flags)
    if lines: return '\n%s' % '\n'.join(lines)
    return '\n\tNone available'
