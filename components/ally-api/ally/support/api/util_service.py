'''
Created on Feb 28, 2012

@package: ally api
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides utility methods for service implementations.
'''

from ally.api.criteria import AsBoolean, AsLike, AsEqual, AsOrdered
from ally.api.extension import IterSlice
from ally.api.operator.type import TypeContainer, TypeModel, TypeService, \
    TypeProperty
from ally.api.type import typeFor
from ally.type_legacy import Iterable, Iterator
from collections import Sized
from itertools import chain
import re

# --------------------------------------------------------------------

def iterateFor(container):
    '''
    Provides the properties names and property types for the provided container object or class.
    
    @param container: container object|class
        The container to provide the properties names for.
    @return: Iterator(tuple(string, TypeProperty))
        The iterator containing the properties names and properties types.
    '''
    ctype = typeFor(container)
    assert isinstance(ctype, TypeContainer), 'Invalid container %s' % ctype
    return ctype.properties.items()

def namesFor(container):
    '''
    Provides the properties names for the provided container object or class.
    
    @param container: container object|class
        The container to provide the properties names for.
    @return: Iterator(string)
        The iterator containing the properties names
    '''
    ctype = typeFor(container)
    assert isinstance(ctype, TypeContainer), 'Invalid query %s' % ctype
    return iter(ctype.properties)

def nameForModel(model):
    '''
    Provides the properties names for the provided model object or class.
    
    @param model: model object|class
        The model to provide the properties names for.
    @return: Iterator(string)
        The iterator containing the properties names
    '''
    mtype = typeFor(model)
    assert isinstance(mtype, TypeModel), 'Invalid model %s' % model
    return mtype.name

def iterateCalls(service):
    '''
    Provides the calls of the service.
    
    @param service: service object|class
        The service to provide the calls for.
    @return: Iterator(Call)
        The iterator containing the calls.
    '''
    stype = typeFor(service)
    assert isinstance(stype, TypeService), 'Invalid service %s' % service
    return (ctype.call for ctype in stype.calls.values())

def isModelId(obj):
    '''
    Checks if the provided property is the id of a model.
    
    @param obj: object
        The object to check.
    @return: boolean
        True if the provided type is the id of a model, False otherwise.
    '''
    prop = typeFor(obj)
    if not isinstance(prop, TypeProperty): return False
    assert isinstance(prop, TypeProperty)
    if not isinstance(prop.parent, TypeModel): return False
    assert isinstance(prop.parent, TypeModel)
    return prop.parent.propertyId == prop

# --------------------------------------------------------------------

def copy(src, dest, exclude=()):
    '''
    Copies the container properties from the object source to object destination, attention only the common properties from
    source and destination will be transfered, the rest of properties will be ignored.
    If common properties are not compatible by types an exception will be raised.
    
    @param src: container object
        The source to copy from.
    @param dest: container object
        The destination to copy to.
    @param exclude: list[string]|tuple(string)
        A list of properties names to exclude from copy.
    @return: container object
        Returns the destination object.
    @raise ValueError: If the common properties are not compatible by type.
    '''
    assert src is not None, 'A source object is required'
    properites = set(namesFor(dest))
    for name, prop in iterateFor(src):
        if name not in properites: continue
        if name in exclude: continue
        if prop in src: setattr(dest, name, getattr(src, name))
    return dest

# --------------------------------------------------------------------

def trimIter(collection, size=None, offset=None, limit=None):
    '''
    Trims the provided iterator based on the offset and limit.
    
    @param collection: list|Iterable|Iterator|Sized
        The iterator to be trimmed.
    @param size: integer|None
        The size of the iterator, None if the collection is a list.
    @param offset: integer
        The offset to trim from
    @param limit: integer
        The limit to trim to.
    @return: generator
        A generator that will provide the trimmed iterator.
    '''
    assert offset is None or isinstance(offset, int), 'Invalid offset %s' % offset
    assert limit is None or isinstance(limit, int), 'Invalid limit %s' % limit
    
    if size is None and isinstance(collection, Sized): size = len(collection)
    assert isinstance(size, int), 'Invalid size %s, size is required if the provided collection is not sized' % size
    
    if offset is None: offset = 0
    else: assert isinstance(offset, int), 'Invalid offset %s' % offset
    if limit is None: limit = size
    else: assert isinstance(limit, int), 'Invalid limit %s' % limit
    
    if isinstance(collection, Iterable): collection = iter(collection)
    assert isinstance(collection, Iterator), 'Invalid iterator %s' % collection

    for _k in zip(range(0, offset), collection): pass
    return (v for v, _k in zip(collection, range(0, limit)))

def processQuery(collection, clazz, query, fetcher=None):
    '''
    Filters the iterable of entities based on the provided query.
    
    @param collection: Iterable(model object of clazz or reference)
        The entities objects iterator to be processed.
    @param clazz: class
        The model class to use the query on.
    @param query: query|None
        The query object to provide filtering on.
    @param fetcher: callable(object) -> object|None
        The callable used in fetching the actual models of clazz in case the collection only contains references
        of the models.
    @return: list[model object of clazz or reference]
        The list of processed entities or references.
    '''
    assert isinstance(collection, Iterable), 'Invalid entities objects iterable %s' % collection
    if query is None:
        if not isinstance(collection, list): collection = list(collection)
        return collection
    
    filtered = list(collection)
    if fetcher:
        items = {}
        def get(reference):
            if reference not in items: items[reference] = fetcher(reference)
            return items[reference]
    else: get = lambda item: item
    
    ordered, unordered = [], []
    properties = {name.lower(): name for name in namesFor(clazz)}
    for cname, criteria in iterateFor(query):
        pname = properties.get(cname.lower())
        if pname is not None and criteria in query:
            cvalue = getattr(query, cname)
            if isinstance(cvalue, AsBoolean):
                assert isinstance(cvalue, AsBoolean)
                if AsBoolean.value in cvalue:
                    filtered = [item for item in filtered if cvalue.value == getattr(get(item), pname)]
            elif isinstance(cvalue, AsLike):
                assert isinstance(cvalue, AsLike)
                regex = None
                if AsLike.like in cvalue:
                    if cvalue.like is not None: regex = likeAsRegex(cvalue.like, False)
                elif AsLike.ilike in cvalue:
                    if cvalue.ilike is not None: regex = likeAsRegex(cvalue.ilike, True)

                if regex is not None:
                    filtered = ((item, getattr(get(item), pname)) for item in filtered)
                    filtered = [item for item, value in filtered if value is not None and regex.match(value)]
            elif isinstance(cvalue, AsEqual):
                assert isinstance(cvalue, AsEqual)
                if AsEqual.equal in cvalue:
                    filtered = [item for item in filtered if cvalue.equal == getattr(get(item), pname)]
            if isinstance(cvalue, AsOrdered):
                assert isinstance(cvalue, AsOrdered)
                if AsOrdered.ascending in cvalue:
                    if AsOrdered.priority in cvalue and cvalue.priority:
                        ordered.append((pname, cvalue.ascending, cvalue.priority))
                    else:
                        unordered.append((pname, cvalue.ascending, None))

            ordered.sort(key=lambda pack: pack[2])
            for prop, asc, __ in reversed(list(chain(ordered, unordered))):
                filtered.sort(key=lambda item: getattr(get(item), prop), reverse=not asc)

    return filtered

def processCollection(collection, clazz, query=None, fetcher=None, offset=0, limit=None, withTotal=False):
    '''
    Process the collection based on the provided parameters.
    
    @param collection: Iterable(model object of clazz or reference)
        The entities objects iterator to be processed.
    @param clazz: class
        The model class to use the query on.
    @param query: query|None
        The query object to provide filtering on.
    @param fetcher: callable(object) -> object|None
        The callable used in fetching the actual models of clazz in case the collection only contains references
        of the models.
        
    ... the options
    
    @return: Iterable(model object of clazz or reference)
        The processed collection.
    '''
    assert isinstance(withTotal, bool), 'Invalid with total flag %s' % withTotal
    collection = processQuery(collection, clazz, query, fetcher)
    total = len(collection)
    collection = trimIter(collection, total, offset, limit)
    if withTotal: return IterSlice(collection, total, offset, limit)
    return collection

# --------------------------------------------------------------------

def likeAsRegex(like, caseInsensitive=True):
    '''
    Transform a like pattern (ex: heloo%world) resembling a database form, to an actual regex that can be used to
    compare strings.
    
    @param like: string
        The like pattern to convert to regex.
    @param caseInsensitive: boolean
        Flag indicating that the regex should be case insensitive.
    @return: regex
        The regex pattern to use.
    '''
    assert isinstance(like, str), 'Invalid like %s' % like
    assert isinstance(caseInsensitive, bool), 'Invalid case insensitive %s' % caseInsensitive
    likeRegex = like.split('%')
    likeRegex = '.*'.join(re.escape(n) for n in likeRegex)
    likeRegex += '$'
    if caseInsensitive: likeRegex = re.compile(likeRegex, re.IGNORECASE)
    else: likeRegex = re.compile(likeRegex)
    return likeRegex
