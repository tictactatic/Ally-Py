'''
Created on Jan 4, 2012

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides utility methods based on the API specifications.
'''

from ally.api.type import Type
from ally.core.spec.resources import Converter
from ally.support.util import firstOf, lastCheck
from collections import Iterable
from datetime import date, datetime, time

# --------------------------------------------------------------------

PRIORITIES = {datetime:1, date:2, time:3, float:4, int:5, bool:6, str:7}
# The default priorities used in the conversion.

# --------------------------------------------------------------------
           
def valueOfAny(converter, value, types, priorities=PRIORITIES):
    '''
    Parses the string value into an object value depending on the provided object types.
    
    @param converter: Converter
        The converter to use for obtaining the value.
    @param value: string
        The string representation of the object to be parsed.
    @param types: Iterable(Type)
        The types of object to which the string should be parsed, in case of multiple types the conversion
        will be made starting from the most complex type to the simplest type.
    @param priorities: dictionary{class: integer}
        The priorities.
    @return: object, type
        The parsed object value and the type that has been successfully parsed for.
    @raise ValueError: In case the parsing was not successful.
    '''
    assert isinstance(converter, Converter), 'Invalid converter %s' % converter
    assert isinstance(value, str), 'Invalid value %s' % value
    assert isinstance(types, Iterable), 'Invalid types %s' % types
    assert isinstance(priorities, dict), 'Invalid priorities %s' % priorities
    if value is None: return None
    
    prioritized = []
    for type in types:
        assert isinstance(type, Type), 'Invalid type %s' % type
        for clazz, priority in priorities.items():
            if type.isOf(clazz):
                prioritized.append((priority, type))
                break
        else: raise ValueError('Invalid object type %s for converter' % type)
    if not prioritized: raise ValueError('No object type provided for converter')
    
    prioritized.sort(key=firstOf)
    for isLast, (_priority, type) in lastCheck(prioritized):
        try: return converter.asValue(value, type), type
        except ValueError:
            if isLast: raise
