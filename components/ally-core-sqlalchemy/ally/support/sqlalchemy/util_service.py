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
from ally.api.type import typeFor
from ally.exception import InputError, Ref
from ally.internationalization import _
from ally.support.api.util_service import namesForQuery
from ally.support.sqlalchemy.mapper import mappingFor
from itertools import chain
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.sql.expression import and_, not_, or_

# --------------------------------------------------------------------

def handle(e, entity):
    '''
    Handles the SQL alchemy exception while inserting or updating.
    '''
    if isinstance(e, IntegrityError):
        raise InputError(Ref(_('Cannot persist, failed unique constraints on entity'), model=typeFor(entity).container))
    if isinstance(e, OperationalError):
        raise InputError(Ref(_('A foreign key is not valid'), model=typeFor(entity).container))
    raise e

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

def buildQuery(sqlQuery, query, mapped, only=None, exclude=None):
    '''
    Builds the query on the SQL alchemy query.
    
    @param sqlQuery: SQL alchemy
        The sql alchemy query to use.
    @param query: query
        The REST query object to provide filtering on.
    @param mapped: class
        The mapped model class to use the query on.
    @param only: tuple(string|TypeCriteriaEntry)|string|TypeCriteriaEntry|None
        The criteria names or references to build the query for, if no criteria is provided then all the query criteria
        are considered.
    @param exclude: tuple(string|TypeCriteriaEntry)|string|TypeCriteriaEntry|None
        The criteria names or references to be excluded when processing the query. If you provided a only parameter you cannot
        provide an exclude.
    '''
    assert query is not None, 'A query object is required'
    clazz = query.__class__

    ordered, unordered = [], []
    mapper = mappingFor(mapped)
    assert isinstance(mapper, Mapper)

    columns = {cp.key.lower(): getattr(mapper.c, cp.key)
                  for cp in mapper.iterate_properties if isinstance(cp, ColumnProperty)}
    columns = {criteria:columns.get(criteria.lower()) for criteria in namesForQuery(clazz)}

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
                assert isinstance(typ, TypeCriteriaEntry), 'Invalid only criteria %s' % criteria
                column = columns.get(criteria)
                assert column is not None, 'Invalid only criteria \'%s\' for query class %s' % (criteria, clazz)
                onlyColumns[criteria] = column
        columns = onlyColumns
    elif exclude:
        if not isinstance(exclude, tuple): exclude = (exclude,)
        for criteria in exclude:
            if isinstance(criteria, str):
                column = columns.pop(criteria, None)
                assert column is not None, 'Invalid exclude criteria name \'%s\' for query class %s' % (criteria, clazz)
            else:
                typ = typeFor(criteria)
                assert isinstance(typ, TypeCriteriaEntry), 'Invalid exclude criteria %s' % criteria
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
        for column, asc, __ in chain(ordered, unordered):
            if asc: sqlQuery = sqlQuery.order_by(column)
            else: sqlQuery = sqlQuery.order_by(column.desc())

    return sqlQuery


def buildPartialQuery(sqlQuery, query, mapped, queryClauses):
    '''
    Builds the query on the SQL alchemy query.
    
    @param sqlQuery: SQL alchemy
        The sql alchemy query to use.
    @param query: query
        The REST query object to provide filtering on.
    @param mapped: class
        The mapped model class to use the query on.
    '''
    assert query is not None, 'A query object is required'
    clazz = query.__class__

    ordered, unordered = [], []
    mapper = mappingFor(mapped)
    assert isinstance(mapper, Mapper)

    properties = {cp.key.lower(): getattr(mapper.c, cp.key)
                  for cp in mapper.iterate_properties if isinstance(cp, ColumnProperty)}
    
    andClauses = list()
    orClauses = list()

    for criteria in namesForQuery(clazz):
        column = properties.get(criteria.lower())
        if column is not None and getattr(clazz, criteria) in query:

            crt = getattr(query, criteria)
            if isinstance(crt, AsBoolean):
                assert isinstance(crt, AsBoolean)
                if AsBoolean.value in crt:
                    if crt.operator == 'or': orClauses.append(column == crt.value)
                    elif crt.operator == 'not': andClauses.append(not_(column == crt.value))
                    else: andClauses.append(column == crt.value)
            elif isinstance(crt, AsLike):
                assert isinstance(crt, AsLike)
                if AsLike.like in crt: 
                    if crt.operator == 'or': orClauses.append(column.like(crt.like))
                    elif crt.operator == 'not': andClauses.append(not_(column.like(crt.like)))
                    else: andClauses.append(column.like(crt.like))
                elif AsLike.ilike in crt: 
                    if crt.operator == 'or': orClauses.append(column.ilike(crt.ilike))
                    elif crt.operator == 'not': andClauses.append(not_(column.ilike(crt.ilike)))
                    else: andClauses.append(column.ilike(crt.ilike))
            elif isinstance(crt, AsEqual):
                assert isinstance(crt, AsEqual)
                if AsEqual.equal in crt:
                    if crt.operator == 'or': orClauses.append(column == crt.equal)
                    elif crt.operator == 'not': andClauses.append(not_(column == crt.equal))
                    else: andClauses.append(column.ilike(column == crt.equal))
            elif isinstance(crt, (AsDate, AsTime, AsDateTime, AsRange)):
                if crt.__class__.start in crt: 
                    if crt.operator == 'or': orClauses.append(column >= crt.start)
                    elif crt.operator == 'not': andClauses.append(not_(column >= crt.start))
                    else: andClauses.append(column.ilike(column >= crt.start))
                elif crt.__class__.until in crt: 
                    if crt.operator == 'or': orClauses.append(column < crt.until)
                    elif crt.operator == 'not': andClauses.append(not_(column < crt.until))
                    else: andClauses.append(column.ilike(column < crt.until))
                if crt.__class__.end in crt: 
                    if crt.operator == 'or': orClauses.append(column <= crt.end)
                    elif crt.operator == 'not': andClauses.append(not_(column <= crt.end))
                    else: andClauses.append(column.ilike(column <= crt.end))
                elif crt.__class__.since in crt: 
                    if crt.operator == 'or': orClauses.append(column > crt.since)
                    elif crt.operator == 'not': andClauses.append(not_(column > crt.since))
                    else: andClauses.append(column.ilike(column > crt.since))

            if isinstance(crt, AsOrdered):
                assert isinstance(crt, AsOrdered)
                if AsOrdered.ascending in crt:
                    if AsOrdered.priority in crt and crt.priority:
                        ordered.append((column, crt.ascending, crt.priority))
                    else:
                        unordered.append((column, crt.ascending, None))

            ordered.sort(key=lambda pack: pack[2])
            for column, asc, __ in chain(ordered, unordered):
                if asc: sqlQuery = sqlQuery.order_by(column)
                else: sqlQuery = sqlQuery.order_by(column.desc())               

    lengthAnd = len(andClauses)
    lengthOr = len(orClauses)
    
    if lengthAnd == 0:
        if lengthOr == 0:
            #do nothing 
            pass
        elif lengthOr == 1:   
            queryClauses.append(orClauses[0])
        elif lengthOr > 1:
            queryClauses.append(or_(*orClauses))
    elif lengthAnd == 1:
        if lengthOr == 0:
            queryClauses.append(andClauses[0])
        elif lengthOr == 1:   
            queryClauses.append(or_(andClauses[0], orClauses[0]))
        elif lengthOr > 1:
            queryClauses.append(or_(andClauses[0], or_(*orClauses)))
    elif lengthAnd > 1:
        if lengthOr == 0:
            queryClauses.append(and_(*andClauses)) 
        elif lengthOr == 1:   
            queryClauses.append(or_(and_(*andClauses), orClauses[0]))
        elif lengthOr > 1:
            queryClauses.append(or_(and_(*andClauses), or_(*orClauses)))

    return sqlQuery
