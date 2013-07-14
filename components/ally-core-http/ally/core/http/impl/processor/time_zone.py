'''
Created on Sep 14, 2012

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the GMT support transformation.
'''

from ally.container.ioc import injected
from ally.core.http.spec.codes import TIME_ZONE_ERROR
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import requires, defines
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.codes import CodedHTTP
from ally.http.spec.headers import HeadersRequire, HeaderRaw
from datetime import datetime, date, tzinfo
from pytz import timezone
from pytz.exceptions import UnknownTimeZoneError

# --------------------------------------------------------------------

TIME_ZONE = HeaderRaw('X-TimeZone')
# The custom time zone header.
CONTENT_TIME_ZONE = HeaderRaw('X-Content-TimeZone')
# The custom content time zone header.
        
# --------------------------------------------------------------------
    
class Request(HeadersRequire):
    '''
    The request converter context.
    '''
    # ---------------------------------------------------------------- Required
    converterContent = requires(Converter)

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    errorMessages = defines(list)

# --------------------------------------------------------------------

@injected
class TimeZoneConverterHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the time zone converter handler.
    '''

    baseTimeZone = 'UTC'
    # The base time zone that the server date/time values are provided.
    defaultTimeZone = 'UTC'
    # The default time zone if none is specified.

    def __init__(self):
        assert isinstance(self.baseTimeZone, str), 'Invalid base time zone %s' % self.baseTimeZone
        assert isinstance(self.defaultTimeZone, str), 'Invalid default time zone %s' % self.defaultTimeZone
        super().__init__()

        self.baseTZ = timezone(self.baseTimeZone)
        self.defaultTZ = timezone(self.defaultTimeZone)

    def process(self, chain, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the time zone support for the request converter.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        
        timeZoneStr = TIME_ZONE.fetch(request)
        if timeZoneStr:
            try: timeZoneStr = timezone(timeZoneStr)
            except UnknownTimeZoneError:
                TIME_ZONE_ERROR.set(response)
                if response.errorMessages is None: response.errorMessages = []
                response.errorMessages.append('Unknown time zone \'%s\'' % timeZoneStr)
                return
        else: timeZoneStr = self.defaultTZ
            
        timeZoneVal = CONTENT_TIME_ZONE.fetch(request)
        if timeZoneVal:
            try: timeZoneVal = timezone(timeZoneVal)
            except UnknownTimeZoneError:
                TIME_ZONE_ERROR.set(response)
                if response.errorMessages is None: response.errorMessages = []
                response.errorMessages.append('Unknown content time zone \'%s\'' % timeZoneVal)
                return
        else: timeZoneVal = self.defaultTZ

        request.converterContent = ConverterTimeZone(request.converterContent, self.baseTZ, timeZoneStr, timeZoneVal)
            
# --------------------------------------------------------------------

class ConverterTimeZone(Converter):
    '''
    Provides the converter time zone support.
    '''
    __slots__ = ('converter', 'baseTimeZone', 'timeZoneStr', 'timeZoneVal')

    def __init__(self, converter, baseTimeZone, timeZoneStr, timeZoneVal):
        '''
        Construct the GMT converter.
        
        @param converter: Converter
            The wrapped converter.
        @param baseTimeZone: tzinfo
            The time zone of the dates to be converted.
        @param timeZoneStr: tzinfo
            The time zone to convert to string values.
        @param timeZoneVal: tzinfo
            The time zone to convert the string values.
        '''
        assert isinstance(converter, Converter), 'Invalid converter %s' % converter
        assert isinstance(baseTimeZone, tzinfo), 'Invalid base time zone %s' % baseTimeZone
        assert isinstance(timeZoneStr, tzinfo), 'Invalid time zone %s' % timeZoneStr
        assert isinstance(timeZoneVal, tzinfo), 'Invalid time zone %s' % timeZoneVal

        self.converter = converter
        self.baseTimeZone = baseTimeZone
        self.timeZoneStr = timeZoneStr
        self.timeZoneVal = timeZoneVal

    def asValue(self, strValue, objType):
        '''
        @see: Converter.asValue
        '''
        objValue = self.converter.asValue(strValue, objType)
        if isinstance(objValue, (date, datetime)):
            objValue = self.baseTimeZone.localize(objValue)
            objValue = objValue.astimezone(self.timeZoneVal)
            objValue = objValue.replace(tzinfo=None)
            # We need to set the time zone to None since the None TX date time generated by SQL alchemy can not be compared
            # with the date times with TZ.
        return objValue

    def asString(self, objValue, objType):
        '''
        @see: Converter.asString
        '''
        if isinstance(objValue, (date, datetime)):
            objValue = self.baseTimeZone.localize(objValue)
            objValue = objValue.astimezone(self.timeZoneStr)
        return self.converter.asString(objValue, objType)
