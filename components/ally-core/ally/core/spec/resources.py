'''
Created on Jun 18, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Module containing specifications for the resources tree.
'''

from ally.api.type import Type
from datetime import date, datetime, time

# --------------------------------------------------------------------

class Converter:
    '''
    Provides the conversion of primitive types to strings in vice versa.
    The converter provides basic conversion, please extend for more complex or custom transformation.
    '''
    __slots__ = ()

    def asString(self, value, type):
        '''
        Converts the provided object to a string. First it will detect the type and based on that it will call
        the corresponding convert method.
        
        @param value: object
            The value to be converted to string.
        @param type: Type
            The type of object to convert the string to.
        @return: string
            The string form of the provided value object.
        '''
        assert isinstance(type, Type), 'Invalid object type %s' % type
        assert value is not None, 'Provide an object value'
        
        if type.isOf(str): return value
        if type.isOf(int) or type.isOf(float): return str(value)
        if type.isOf(bool): return 'true' if value is True else 'false'
        if type.isOf(datetime):
            assert isinstance(value, datetime), 'Invalid value %s for type %s' % (value, type)
            return value.strftime('%Y-%m-%dT%H:%M:%SZ')
        if type.isOf(date):
            assert isinstance(value, date), 'Invalid value %s for type %s' % (value, type)
            return value.strftime('%Y-%m-%d')
        if type.isOf(time):
            assert isinstance(value, time), 'Invalid value %s for type %s' % (value, type)
            return value.strftime('%H:%M:%S')
        raise ValueError('Invalid object type %s for converter' % type)

    def asValue(self, value, type):
        '''
        Parses the string value into an object value depending on the provided object type.
        
        @param value: string
            The string representation of the object to be parsed.
        @param type: Type
            The type of object to which the string should be parsed.
        @return: object
            The parsed value.
        @raise ValueError: In case the parsing was not successful.
        '''
        assert isinstance(type, Type), 'Invalid object type %s' % type
        if value is None: return None
        assert isinstance(value, str), 'Invalid value %s' % value
        
        if type.isOf(str): return value
        if type.isOf(int): return int(value)
        if type.isOf(float): return float(value)
        if type.isOf(bool):
            if value.strip().lower() == 'true': return True
            elif value.strip().lower() == 'false': return False
            raise ValueError('Invalid boolean value \'%s\'' % value)
        if type.isOf(datetime): return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        if type.isOf(date): return datetime.strptime(value, '%Y-%m-%d').date()
        if type.isOf(time): return time.strptime(value, '%H:%M:%S').time()
        raise ValueError('Invalid object type %s for converter' % type)
