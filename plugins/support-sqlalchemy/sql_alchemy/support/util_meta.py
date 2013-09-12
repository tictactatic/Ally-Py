'''
Created on Aug 30, 2013

@package: support sqlalchemy
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides utility methods for SQL alchemy meta definitions.
'''

from .mapper import mappingFor, tableFor
from ally.api.operator.type import TypeModel, TypeProperty
from ally.api.type import typeFor
from ally.support.util import modifyFirst, toUnderscore
from ally.support.util_sys import callerLocals
from collections import OrderedDict
from inspect import isclass
from operator import attrgetter
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, mapper, column_property
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql import expression
from sqlalchemy.sql.expression import join, select
from sqlalchemy.types import DateTime, TypeDecorator, String
import json


# --------------------------------------------------------------------

class JSONEncodedDict(TypeDecorator):
    '''
    Provides a JSON dictionary type encoded.
    @see: http://docs.sqlalchemy.org/en/rel_0_8/core/types.html#marshal-json-strings
    '''

    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None: return json.dumps(value, sort_keys=True)

    def process_result_value(self, value, dialect):
        if value is not None: return json.loads(value, object_hook=OrderedDict)

# --------------------------------------------------------------------

def hybrid(*args, fset=None, fdel=None, expr=None):
    '''
    Method used to facilitate the use of @see: hybrid_property
    '''
    def decorator(fget): return hybrid_property(fget, fset, fdel, expr)
    if not args: return decorator
    return decorator(*args)

def relationshipModel(mappedId, *spec):
    '''
    Creates a relationship with the model, this should only be used in case the mapped model database id is different from the
    actual model id.
    
    @param mappedId: InstrumentedAttribute
        The mapped model id to create the relation with.
    @param spec: arguments containing
        column: string
            The column name containing the foreign key relation, attention if target is provided then
            also column needs to be provided, if None provided it will create one automatically.
        target: string
            The SQL alchemy relationship target name, if None provided it will create one automatically.
    '''
    assert isinstance(mappedId, InstrumentedAttribute), 'Invalid mapped id %s' % mappedId
    register = callerLocals()
    assert '__module__' in register, 'This function should only be used inside meta class definitions'
    rtype = typeFor(mappedId.class_)
    assert isinstance(rtype, TypeModel), 'Invalid class %s' % mappedId.class_
    assert isinstance(rtype.propertyId, TypeProperty), 'No property id for %s' % rtype
    assert rtype.propertyId.name != mappedId.property.key, 'Same database id with the model id \'%s\' for %s' % mappedId.class_
    
    column = target = None
    if spec:
        column, *spec = spec
        assert isinstance(column, str), 'Invalid column %s' % column
        if spec:
            target, = spec
            assert isinstance(target, str) and target, 'Invalid target %s' % target
    
    if target is None:
        target = modifyFirst(rtype.name, False)
        if column is None:
            column = '%sId' % target
            register[column] = Column('fk_%s_id' % toUnderscore(target), ForeignKey(mappedId, ondelete='CASCADE'), nullable=False)
        register[target] = relationship(mappedId.class_, uselist=False, lazy='joined', viewonly=True)
    
    def fget(self):
        rel = getattr(self, target)
        if rel: return getattr(rel, rtype.propertyId.name)
    
    def fset(self, value): setattr(self, column, select([mappedId], getattr(mappedId.class_, rtype.propertyId.name) == value))
    
    return hybrid_property(fget, fset, expr=joinedExpr(mappedId.class_, rtype.propertyId.name))

# --------------------------------------------------------------------

def joinedExpr(other, attr):
    '''
    Creates a joined expression.
    @see: joined
    
    @param attr: string
        The attribute name to fetch from the joined class.
    @return: InstrumentedAttribute
        The joined attribute.
    '''
    assert isclass(other), 'Invalid other class %s' % other
    assert isinstance(attr, str), 'Invalid attribute %s' % attr
    
    getter = attrgetter('%s_%s' % (other.__name__, attr))
    def expr(cls): return getter(joined(cls, other))
    return expr

def joined(mapped, other):
    '''
    Creates a joined mapped for the provided mapped class with other class. The joined mapped class will be cached on
    the other class.
    
    @param mapped: class
        The mapped class to create the joined mapped class with.
    @param other: class
        The other class to create the joined mapping with.
    @return: class
        The joined mapped class.
    '''
    assert isclass(mapped), 'Invalid mapped class %s' % mapped
    assert isclass(other), 'Invalid other class %s' % other
    
    name = '%s%s' % (mapped.__name__, other.__name__)
    try: return getattr(mapped, name)
    except AttributeError: pass
    
    properties = {}
    mapping, omapping = mappingFor(mapped), mappingFor(other)
    for cp in mapping.iterate_properties:
        if not isinstance(cp, ColumnProperty) or not cp.key: continue
        assert isinstance(cp, ColumnProperty)
        properties['%s_%s' % (mapped.__name__, cp.key)] = column_property(getattr(mapping.c, cp.key))
    for cp in omapping.iterate_properties:
        if not isinstance(cp, ColumnProperty) or not cp.key: continue
        assert isinstance(cp, ColumnProperty)
        properties['%s_%s' % (other.__name__, cp.key)] = column_property(getattr(omapping.c, cp.key))
    
    
    clazz = type(name, (object,), {})
    mapper(clazz, join(tableFor(mapped), tableFor(other)), properties=properties)
    setattr(mapped, name, clazz)
    
    return clazz

# --------------------------------------------------------------------

class UtcNow(expression.FunctionElement):
    '''
    A function that works like “CURRENT_TIMESTAMP” except applies the appropriate
    conversions so that the time is in UTC time.
    @see: http://docs.sqlalchemy.org/en/latest/core/compiler.html at Further Examples
    '''
    type = DateTime()

@compiles(UtcNow, 'postgresql')
def pgUtcNow(element, compiler, **kw): return 'TIMEZONE(\'utc\', CURRENT_TIMESTAMP)'
@compiles(UtcNow, 'mssql')
def mssqlUtcNow(element, compiler, **kw): return 'GETUTCDATE()'
@compiles(UtcNow, 'sqlite')
def sqliteUtcNow(element, compiler, **kw): return 'datetime(\'now\',\'localtime\')'
