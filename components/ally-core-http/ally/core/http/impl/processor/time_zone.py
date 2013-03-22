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
from ally.core.spec.transform.render import Object, List
from ally.design.processor.attribute import requires, defines
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessorProceed
from ally.http.spec.server import IDecoderHeader
from datetime import datetime, date, tzinfo
from pytz import timezone, common_timezones
from pytz.exceptions import UnknownTimeZoneError

# --------------------------------------------------------------------

class TimeZoneConfigurations:
    '''
    Provides general time zone configurations.
    '''

    nameTimeZone = str
    # The header name where the time zone is set.
    baseTimeZone = 'UTC'
    # The base time zone that the server date/time values are provided.
    defaultTimeZone = 'UTC'
    # The default time zone if none is specified.

    def __init__(self):
        assert isinstance(self.nameTimeZone, str), 'Invalid time zone header name %s' % self.nameTimeZone
        assert isinstance(self.baseTimeZone, str), 'Invalid base time zone %s' % self.baseTimeZone
        assert isinstance(self.defaultTimeZone, str), 'Invalid default time zone %s' % self.defaultTimeZone

        self.baseTZ = timezone(self.baseTimeZone)
        self.defaultTZ = timezone(self.defaultTimeZone)
        
# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    decoderHeader = requires(IDecoderHeader)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(str)
    status = defines(int)
    isSuccess = defines(bool)
    errorMessage = defines(str)
    errorDetails = defines(Object)
    
class RequestConverter(Request):
    '''
    The request converter context.
    '''
    # ---------------------------------------------------------------- Required
    converter = requires(Converter)

class ResponseConverter(Response):
    '''
    The response converter context.
    '''
    # ---------------------------------------------------------------- Required
    converter = requires(Converter)

# --------------------------------------------------------------------

@injected
class TimeZoneConverterRequestHandler(HandlerProcessorProceed, TimeZoneConfigurations):
    '''
    Implementation for a processor that provides the time zone request converter handler.
    '''

    nameTimeZone = 'X-TimeZone'
    # The header name where the time zone is set.

    def __init__(self):
        TimeZoneConfigurations.__init__(self)
        HandlerProcessorProceed.__init__(self)

    def process(self, request:RequestConverter, response:Response, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the time zone support for the request converter.
        '''
        assert isinstance(request, RequestConverter), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid header decoder %s' % request.decoderHeader

        timeZone = request.decoderHeader.retrieve(self.nameTimeZone)
        if timeZone:
            try: timeZone = timezone(timeZone)
            except UnknownTimeZoneError:
                response.code, response.status, response.isSuccess = TIME_ZONE_ERROR
                response.errorMessage = 'Invalid content time zone \'%s\'' % timeZone

                samples = (Object('timezone', attributes={'name', name}) for name in common_timezones)
                response.errorDetails = Object('timezone', List('sample', *samples))
                return

        if timeZone is not None:
            request.converter = ConverterTimeZone(request.converter, self.baseTZ, timeZone)
        else:
            request.converter = ConverterTimeZone(request.converter, self.baseTZ, self.defaultTZ)

@injected
class TimeZoneConverterResponseHandler(HandlerProcessorProceed, TimeZoneConfigurations):
    '''
    Implementation for a processor that provides the time zone response converter handler.
    '''

    nameTimeZone = 'X-Content-TimeZone'
    # The header name where the content time zone is set.

    def __init__(self):
        TimeZoneConfigurations.__init__(self)
        HandlerProcessorProceed.__init__(self)

    def process(self, request:Request, response:ResponseConverter, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Provides the time zone support for the response converter.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, ResponseConverter), 'Invalid response %s' % response
        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid header decoder %s' % request.decoderHeader

        timeZone = request.decoderHeader.retrieve(self.nameTimeZone)
        if timeZone:
            try: timeZone = timezone(timeZone)
            except UnknownTimeZoneError:
                response.code, response.status, response.isSuccess = TIME_ZONE_ERROR
                response.errorMessage = 'Invalid time zone \'%s\'' % timeZone

                samples = (Object('timezone', attributes={'name', name}) for name in common_timezones)
                response.errorDetails = Object('timezone', List('sample', *samples))
                return

        if timeZone is not None:
            response.converter = ConverterTimeZone(response.converter, self.baseTZ, timeZone)
        else:
            response.converter = ConverterTimeZone(response.converter, self.baseTZ, self.defaultTZ)
            
# --------------------------------------------------------------------

class ConverterTimeZone(Converter):
    '''
    Provides the converter time zone support.
    '''
    __slots__ = ('converter', 'baseTimeZone', 'timeZone')

    def __init__(self, converter, baseTimeZone, timeZone):
        '''
        Construct the GMT converter.
        
        @param converter: Converter
            The wrapped converter.
        @param baseTimeZone: tzinfo
            The time zone of the dates to be converted.
        @param timeZone: tzinfo|None
            The time zone to convert to.
        '''
        assert isinstance(converter, Converter), 'Invalid converter %s' % converter
        assert isinstance(baseTimeZone, tzinfo), 'Invalid base time zone %s' % baseTimeZone
        assert isinstance(timeZone, tzinfo), 'Invalid time zone %s' % timeZone

        self.converter = converter
        self.baseTimeZone = baseTimeZone
        self.timeZone = timeZone

    def asValue(self, strValue, objType):
        '''
        @see: Converter.asValue
        '''
        objValue = self.converter.asValue(strValue, objType)
        if isinstance(objValue, (date, datetime)):
            objValue = self.baseTimeZone.localize(objValue)
            objValue = objValue.astimezone(self.timeZone)
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
            objValue = objValue.astimezone(self.timeZone)
        return self.converter.asString(objValue, objType)
