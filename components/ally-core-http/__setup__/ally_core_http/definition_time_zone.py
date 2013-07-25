'''
Created on Jul 17, 2013

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the time zone header definitions.
'''

from ..ally_core.definition import definitions, defin, errors, error, desc
from .definition_header import CATEGORY_HEADER, VERIFY_CATEGORY, \
    updateDescriptionsForHeaders
from ally.container import ioc
from ally.core.http.spec.codes import TIME_ZONE_ERROR
from ally.core.impl.definition import Name

# --------------------------------------------------------------------

try: import pytz  # @UnusedImport
except ImportError: pass
else:
    from pytz import all_timezones
    from ally.core.http.impl.processor.time_zone import TIME_ZONE, CONTENT_TIME_ZONE
    from .processor_time_zone import default_time_zone

    # --------------------------------------------------------------------
    
    VERIFY_TIME_ZONE = Name(TIME_ZONE.name) & VERIFY_CATEGORY
    VERIFY_CONTENT_TIME_ZONE = Name(CONTENT_TIME_ZONE.name) & VERIFY_CATEGORY

    # --------------------------------------------------------------------
    
    @ioc.before(definitions)
    def updateDefinitionsForTimeZone():
        defin(category=CATEGORY_HEADER, name=TIME_ZONE.name)
        defin(category=CATEGORY_HEADER, name=CONTENT_TIME_ZONE.name)
        
    @ioc.before(errors)
    def updateDefinitionErrorForTimeZone():
        error(TIME_ZONE_ERROR.code, VERIFY_TIME_ZONE | VERIFY_CONTENT_TIME_ZONE, 'The time zone headers')
        
    @ioc.before(updateDescriptionsForHeaders)
    def updateDescriptionsForTimeZone():
        sample, curr = [], None
        for tz in all_timezones:
            if curr != tz[:1]:
                sample.append(tz)
                curr = tz[:1]

        # This is based on @see: updateDefinitionsForTimeZone().
        desc(Name(TIME_ZONE.name),
             'the time zone to render the time stamps in, as an example:\n%(sample)s',
             'the default time zone is %(default)s', sample=sample, default=default_time_zone())
        desc(Name(CONTENT_TIME_ZONE.name),
             'the same as \'%(name)s\' but for parsed content', name=TIME_ZONE.name)
