'''
Created on Jan 5, 2012

@package: ally core sql alchemy
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides utility methods for SQL alchemy service implementations.
'''

from ally.api.criteria import AsLike, AsOrdered, AsBoolean, AsEqual, AsDate, \
    AsTime, AsDateTime, AsRange
from ally.api.error import InvalidIdError
from ally.api.extension import IterSlice
from ally.api.operator.type import TypeProperty, TypeCriteria, TypeModel
from ally.api.type import typeFor
from ally.support.api.util_service import namesFor
from ally.support.sqlalchemy.mapper import MappedSupport, mappingFor
from ally.support.sqlalchemy.session import openSession
from inspect import isclass
from itertools import chain
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.schema import Column

# --------------------------------------------------------------------

def buildLimits(sqlQuery, offset=None, limit=None):
    '''
    Builds limiting on the SQL alchemy query.

    @param offset: integer|None
        The offset to fetch elements from.
    @param limit: integer|None
        The limit of elements to get.
    '''
    if offset is not None: sqlQuery = sqlQuery.offset(offset)
    if limit is not None: sqlQuery = sqlQuery.limit(limit)
    return sqlQuery

def buildQuery(sqlQuery, query, Mapped, only=None, exclude=None):
    '''
    Builds the query on the SQL alchemy query.

    @param sqlQuery: SQL alchemy
        The sql alchemy query to use.
    @param query: query
        The REST query object to provide filtering on.
    @param Mapped: class
        The mapped model class to use the query on.
    @param only: tuple(string|TypeCriteriaEntry)|string|TypeCriteriaEntry|None
        The criteria names or references to build the query for, if no criteria is provided then all the query criteria
        are considered.
    @param exclude: tuple(string|TypeCriteriaEntry)|string|TypeCriteriaEntry|None
        The criteria names or references to be excluded when processing the query. If you provided a only parameter you cannot
        provide an exclude.
    '''
    assert query is not None, 'A query object is required'
    clazz, mapper = query.__class__, mappingFor(Mapped)
    assert isinstance(mapper, Mapper), 'Invalid mapper %s' % mapper
    
    columns, ordered, unordered = {}, [], []
    for name in namesFor(Mapped):
        cp, name = mapper.columns.get(name), '%s%s' % (name[0].lower(), name[1:])
        if isinstance(cp, ColumnElement): columns[name] = cp
    columns = {name:columns.get(name) for name in namesFor(clazz)}

    if only:
        if not isinstance(only, tuple): only = (only,)
        assert not exclude, 'Cannot have only \'%s\' and exclude \'%s\' criteria at the same time' % (only, exclude)
        onlyColumns = {}
        for criteria in only:
            if isinstance(criteria, str):
                column = columns.get(criteria)
                assert column is not None, 'Invalid only criteria name \'%s\' for query class %s' % (criteria, clazz)
                onlyColumns[criteria] = column
            else:
                typ = typeFor(criteria)
                assert isinstance(typ, TypeProperty), 'Invalid only criteria %s' % criteria
                assert isinstance(typ.type, TypeCriteria), 'Invalid only criteria %s' % criteria
                column = columns.get(typ.name)
                assert column is not None, 'Invalid only criteria \'%s\' for query class %s' % (criteria, clazz)
                onlyColumns[typ.name] = column
        columns = onlyColumns
    elif exclude:
        if not isinstance(exclude, tuple): exclude = (exclude,)
        for criteria in exclude:
            if isinstance(criteria, str):
                column = columns.pop(criteria, None)
                assert column is not None, 'Invalid exclude criteria name \'%s\' for query class %s' % (criteria, clazz)
            else:
                typ = typeFor(criteria)
                assert isinstance(typ, TypeProperty), 'Invalid exclude criteria %s' % criteria
                assert isinstance(typ.type, TypeCriteria), 'Invalid only criteria %s' % criteria
                column = columns.pop(typ.name, None)
                assert column is not None, 'Invalid exclude criteria \'%s\' for query class %s' % (criteria, clazz)

    for criteria, column in columns.items():
        if column is None or getattr(clazz, criteria) not in query: continue

        crt = getattr(query, criteria)
        if isinstance(crt, AsBoolean):
            assert isinstance(crt, AsBoolean)
            if AsBoolean.value in crt:
                sqlQuery = sqlQuery.filter(column == crt.value)
        elif isinstance(crt, AsLike):
            assert isinstance(crt, AsLike)
            if AsLike.like in crt: sqlQuery = sqlQuery.filter(column.like(crt.like))
            elif AsLike.ilike in crt: sqlQuery = sqlQuery.filter(column.ilike(crt.ilike))
        elif isinstance(crt, AsEqual):
            assert isinstance(crt, AsEqual)
            if AsEqual.equal in crt:
                sqlQuery = sqlQuery.filter(column == crt.equal)
        elif isinstance(crt, (AsDate, AsTime, AsDateTime, AsRange)):
            if crt.__class__.start in crt: sqlQuery = sqlQuery.filter(column >= crt.start)
            elif crt.__class__.until in crt: sqlQuery = sqlQuery.filter(column < crt.until)
            if crt.__class__.end in crt: sqlQuery = sqlQuery.filter(column <= crt.end)
            elif crt.__class__.since in crt: sqlQuery = sqlQuery.filter(column > crt.since)

        if isinstance(crt, AsOrdered):
            assert isinstance(crt, AsOrdered)
            if AsOrdered.ascending in crt:
                if AsOrdered.priority in crt and crt.priority:
                    ordered.append((column, crt.ascending, crt.priority))
                else:
                    unordered.append((column, crt.ascending, None))

        ordered.sort(key=lambda pack: pack[2])
        for column, asc, _priority in chain(ordered, unordered):
            if asc: sqlQuery = sqlQuery.order_by(column)
            else: sqlQuery = sqlQuery.order_by(column.desc())

    return sqlQuery

def iterateObjectCollection(sqlQuery, offset=None, limit=None, withTotal=False):
    '''
    Iterates the collection of objects from the sql query based on the provided parameters.
    
    @param sqlQuery: SQL alchemy
        The sql alchemy query to iterate the collection from.
        
    ... the options
    
    @return: Iterable(object)
        The obtained collection of objects.
    '''
    if withTotal:
        sqlLimit = buildLimits(sqlQuery, offset, limit)
        if limit <= 0: return (), sqlQuery.count()
        return IterSlice(sqlLimit.all(), sqlQuery.count(), offset, limit)
    return sqlQuery.all()

def iterateCollection(sqlQuery, offset=None, limit=None, withTotal=False):
    '''
    Iterates the collection of value from the sql query based on the provided parameters.
    
    @param sqlQuery: SQL alchemy
        The sql alchemy query to iterate the collection from.
        
    ... the options
    
    @return: Iterable(object)
        The obtained collection of values.
    '''
    if withTotal:
        sqlLimit = buildLimits(sqlQuery, offset, limit)
        if limit == 0: return (), sqlQuery.count()
        return IterSlice((value for value, in sqlLimit.all()), sqlQuery.count(), offset, limit)
    return (value for value, in sqlQuery.all())

# --------------------------------------------------------------------

def insertModel(Mapped, model):
    '''
    Inserts the provided model entity using the current session.

    @param Mapped: class
        The mapped class to insert the model for.
    @param model: object
        The model to insert.
    @return: object
        The database model that has been inserted.
    '''
    assert isclass(Mapped), 'Invalid class %s' % Mapped
    assert isinstance(Mapped, MappedSupport), 'Invalid mapped class %s' % Mapped
    if isinstance(model, Mapped): dbModel = model
    else:
        typ, mapper = typeFor(Mapped), mappingFor(Mapped)
        assert isinstance(typ, TypeModel), 'Invalid model class %s' % Mapped
        assert isinstance(mapper, Mapper), 'Invalid mapper %s' % mapper
        assert typ.isOf(model), 'Invalid model %s for %s' % (model, typ)
        
        dbModel = Mapped()
        for name, prop in typ.properties.items():
            if not isinstance(mapper.columns.get(name), ColumnElement): continue
            if prop in model: setattr(dbModel, name, getattr(model, name))
    
    openSession().add(dbModel)
    openSession().flush((dbModel,))
    return dbModel

def updateModel(Mapped, model):
    '''
    Updates the provided model entity using the current session.

    @param Mapped: class
        The mapped class to update the model for, the model type is required to have a property id.
    @param model: object
        The model to be updated.
    @return: object
        The database model that has been updated.
    '''
    assert isclass(Mapped), 'Invalid class %s' % Mapped
    assert isinstance(Mapped, MappedSupport), 'Invalid mapped class %s' % Mapped
    if isinstance(model, Mapped):
        dbModel = model
        openSession().merge(dbModel)
    else:
        typ = typeFor(Mapped)
        assert isinstance(typ, TypeModel), 'Invalid model class %s' % Mapped
        assert typ.isOf(model), 'Invalid model %s for %s' % (model, typ)
        assert isinstance(typ.propertyId, TypeProperty), 'Invalid property id of %s' % typ
        
        dbModel = openSession().query(Mapped).get(getattr(model, typ.propertyId.name))
        if not dbModel: raise InvalidIdError(typ.propertyId)
        for name, prop in typ.properties.items():
            if not isinstance(getattr(Mapped, name), ColumnElement): continue
            if prop in model: setattr(dbModel, name, getattr(model, name))
    
    openSession().flush((dbModel,))
    return dbModel
